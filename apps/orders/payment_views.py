# -*- coding: utf-8 -*-
"""
Модуль для обробки онлайн оплати через Portmone та інші сервіси
"""

import hashlib
import hmac
import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from .models import Order, PaymentTransaction


# ========== НАЛАШТУВАННЯ PORTMONE ==========
# Отримай ці дані після реєстрації на https://www.portmone.com.ua/
PORTMONE_PAYEE_ID = getattr(settings, 'PORTMONE_PAYEE_ID', 'YOUR_PAYEE_ID')
PORTMONE_LOGIN = getattr(settings, 'PORTMONE_LOGIN', 'YOUR_LOGIN')
PORTMONE_PASSWORD = getattr(settings, 'PORTMONE_PASSWORD', 'YOUR_PASSWORD')
PORTMONE_API_URL = 'https://www.portmone.com.ua/gateway/'


def generate_portmone_signature(params, password):
    """
    Генерує підпис для Portmone згідно їхньої документації
    """
    # Сортуємо параметри за ключами
    sorted_params = sorted(params.items())
    # Створюємо рядок для підпису
    sign_string = ';'.join([f"{k}={v}" for k, v in sorted_params])
    sign_string += f";{password}"
    
    # SHA256 хеш
    signature = hashlib.sha256(sign_string.encode('utf-8')).hexdigest()
    return signature


@login_required
def payment_page(request, order_id):
    """
    Сторінка оплати замовлення
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Створюємо транзакцію
    transaction = PaymentTransaction.objects.create(
        order=order,
        transaction_type='payment',
        status='initiated',
        amount=order.total_amount,
        currency='UAH',
        payment_system='portmone'
    )
    print(f"✅ Створено транзакцію #{transaction.id} для замовлення #{order.order_number or order.id}")
    
    # Перевіряємо що замовлення потребує оплати
    if order.payment_method != 'card_online':
        return redirect('orders:detail', pk=order.id)
    
    # Якщо вже оплачено
    if order.payment_status == 'paid':
        return redirect('orders:payment_success', order_id=order.id)
    
    # Підготовка даних для платіжної форми
    amount = float(order.total_amount)
    
    # Параметри для Portmone
    portmone_params = {
        'payee_id': PORTMONE_PAYEE_ID,
        'shop_order_number': str(order.order_number or order.id),
        'bill_amount': f"{amount:.2f}",
        'description': f"Оплата замовлення №{order.order_number or order.id}",
        'success_url': request.build_absolute_uri(reverse('orders:payment_success', kwargs={'order_id': order.id})),
        'failure_url': request.build_absolute_uri(reverse('orders:payment_failure', kwargs={'order_id': order.id})),
        'result_url': request.build_absolute_uri(reverse('orders:payment_callback')),
        'lang': 'uk',
    }
    
    # Генеруємо підпис (якщо потрібно згідно документації)
    # portmone_params['signature'] = generate_portmone_signature(portmone_params, PORTMONE_PASSWORD)
    
    context = {
        'order': order,
        'portmone_url': PORTMONE_API_URL,
        'portmone_params': portmone_params,
        'amount': amount,
    }
    
    return render(request, 'zoosvit/orders/payment.html', context)


@login_required
def payment_success(request, order_id):
    """
    Сторінка успішної оплати
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Оновлюємо статус оплати (якщо ще не оновлено callback'ом)
    if order.payment_status == 'pending':
        order.payment_status = 'paid'
        order.save()
        
        # Оновлюємо транзакцію
        transaction = order.transactions.filter(status='initiated').order_by('-created_at').first()
        if transaction:
            transaction.mark_as_success()
        
        # Відправляємо email
        send_payment_success_email(order)
    
    context = {
        'order': order,
    }
    
    return render(request, 'zoosvit/orders/payment_success.html', context)


@login_required
def payment_failure(request, order_id):
    """
    Сторінка невдалої оплати
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Оновлюємо статус оплати
    if order.payment_status == 'pending':
        order.payment_status = 'failed'
        order.save()
        
        # Оновлюємо транзакцію
        transaction = order.transactions.filter(status='initiated').order_by('-created_at').first()
        if transaction:
            transaction.mark_as_failed('Оплата не пройшла через Portmone')
    
    context = {
        'order': order,
    }
    
    return render(request, 'zoosvit/orders/payment_failure.html', context)


@csrf_exempt
@require_POST
def payment_callback(request):
    """
    Callback від Portmone для підтвердження оплати
    Portmone відправляє POST запит з результатом транзакції
    """
    try:
        # Отримуємо дані від Portmone
        data = request.POST.dict()
        
        # Логування для дебагу
        print(f"📥 Portmone callback: {data}")
        
        # Витягуємо параметри (назви полів можуть відрізнятися, дивись документацію Portmone)
        shop_order_number = data.get('SHOPORDERNUMBER') or data.get('shop_order_number')
        status = data.get('RESULT') or data.get('status')
        payment_id = data.get('APPROVALCODE') or data.get('payment_id')
        
        # Знаходимо замовлення
        order = Order.objects.filter(order_number=shop_order_number).first()
        if not order:
            # Можливо ID передано без префіксу
            try:
                order = Order.objects.get(id=int(shop_order_number))
            except (ValueError, Order.DoesNotExist):
                return HttpResponse('Order not found', status=404)
        
        # Створюємо транзакцію callback
        callback_transaction = PaymentTransaction.objects.create(
            order=order,
            transaction_type='callback',
            status='processing',
            amount=order.total_amount,
            currency='UAH',
            payment_system='portmone',
            external_id=payment_id,
            request_data=data
        )
        
        # Оновлюємо статус оплати
        if status == '0' or status == 'success':  # Успішна оплата (перевір в документації)
            order.payment_status = 'paid'
            order.payment_id = payment_id
            order.save()
            
            callback_transaction.mark_as_success(response_data=data)
            
            # Оновлюємо основну транзакцію
            main_transaction = order.transactions.filter(
                transaction_type='payment',
                status='initiated'
            ).order_by('-created_at').first()
            if main_transaction:
                main_transaction.external_id = payment_id
                main_transaction.mark_as_success(response_data=data)
            
            # Відправляємо email
            send_payment_success_email(order)
            
            print(f"✅ Оплата успішна для замовлення #{order.order_number}")
        else:
            order.payment_status = 'failed'
            order.save()
            
            error_msg = data.get('ERROR_MESSAGE', 'Оплата не пройшла')
            callback_transaction.mark_as_failed(error_message=error_msg, response_data=data)
            
            print(f"❌ Оплата неуспішна для замовлення #{order.order_number}")
        
        return HttpResponse('OK')
        
    except Exception as e:
        print(f"❌ Помилка в payment_callback: {e}")
        return HttpResponse('Error', status=500)


# ========== GOOGLE PAY INTEGRATION ==========

@login_required
def google_pay_init(request, order_id):
    """
    Ініціалізація оплати через Google Pay
    Для роботи Google Pay потрібно:
    1. Підключити Google Pay API в Google Cloud Console
    2. Налаштувати merchant ID
    3. Інтегрувати з платіжним провайдером (наприклад, Portmone)
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.payment_method != 'card_online':
        return JsonResponse({'error': 'Invalid payment method'}, status=400)
    
    # Підготовка даних для Google Pay
    amount = float(order.total_amount)
    
    payment_data = {
        'order_id': order.id,
        'order_number': order.order_number or str(order.id),
        'amount': amount,
        'currency': 'UAH',
        'description': f"Оплата замовлення №{order.order_number or order.id}",
    }
    
    return JsonResponse(payment_data)


# ========== ДОПОМІЖНІ ФУНКЦІЇ ==========

def create_payment_link(order):
    """
    Створює посилання на оплату для замовлення
    """
    payment_url = f"{PORTMONE_API_URL}?"
    params = {
        'payee_id': PORTMONE_PAYEE_ID,
        'shop_order_number': str(order.order_number or order.id),
        'bill_amount': f"{float(order.total_amount):.2f}",
        'description': f"Замовлення №{order.order_number or order.id}",
        'lang': 'uk',
    }
    
    # Додаємо параметри до URL
    param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return payment_url + param_string


def send_payment_success_email(order):
    """
    Відправляє email про успішну оплату
    """
    try:
        subject = f'✅ Оплата успішна - Замовлення №{order.order_number or order.id}'
        
        # Контекст для шаблону
        context = {
            'order': order,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            'admin_email': getattr(settings, 'ADMIN_EMAIL', 'admin@laskazoo.com'),
        }
        
        # HTML версія
        html_content = render_to_string('zoosvit/emails/payment_success.html', context)
        
        # Текстова версія
        text_content = f"""
        Вітаємо, {order.full_name}!
        
        Дякуємо за ваше замовлення! Оплата пройшла успішно.
        
        Замовлення №{order.order_number or order.id}
        Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}
        Сума: {order.total_amount} грн
        
        Найближчим часом наш менеджер зв'яжеться з вами.
        
        З повагою,
        Команда Laskazoo
        """
        
        # Створюємо email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@laskazoo.com'),
            to=[order.email]
        )
        
        # Додаємо HTML версію
        email.attach_alternative(html_content, "text/html")
        
        # Відправляємо
        email.send(fail_silently=True)
        
        print(f"✉️  Email про успішну оплату відправлено на {order.email}")
        return True
        
    except Exception as e:
        print(f"❌ Помилка відправки email: {e}")
        return False
