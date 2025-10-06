from decimal import Decimal
from typing import List, Dict

from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import hashlib
import hmac
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from django.conf import settings
from datetime import datetime, timedelta

from .models import Order, OrderItem
from .forms import OrderCheckoutForm
from apps.products.models import Product, Product_Variant
from .novaposhta_service import nova_poshta_api

from .session_cart import summary as sess_summary, add_item as sess_add, CART_KEY


def ensure_clean_cart(user):
    """
    Гарантує чистий кошик для користувача
    Видаляє всі кошикові замовлення з заповненими даними
    """
    # Шукаємо кошикові замовлення з заповненими контактами
    problematic_carts = Order.objects.filter(
        user=user,
        status=Order.STATUS_CART
    ).exclude(
        full_name='',
        phone='',
        email=''
    )
    
    if problematic_carts.exists():
        print(f"ВИПРАВЛЕННЯ: знайдено {problematic_carts.count()} проблемних кошиків")
        for cart in problematic_carts:
            print(f"   Видаляємо кошик #{cart.id} з контактами: {cart.full_name}")
            cart.delete()
    
    return True


def _is_ajax(request):
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.headers.get('HX-Request') == 'true'
        or request.GET.get('ajax') == '1'
    )

def _get_cart(user):
    return Order.objects.filter(user=user, status=Order.STATUS_CART).first()

def _cart_tuple(user):
    order = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
    total = Decimal('0')
    if order:
        line_total = ExpressionWrapper(
            F('quantity') * F('retail_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
        total = order.items.aggregate(total=Sum(line_total))['total'] or Decimal('0')
    return order, total

def _cart_math(user):
    order = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
    if not order:
        return 0, 0, Decimal('0')
    qty = order.items.aggregate(q=Sum('quantity'))['q'] or 0
    line_total = ExpressionWrapper(
        F('quantity') * F('retail_price'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    total = order.items.aggregate(t=Sum(line_total))['t'] or Decimal('0')
    count = order.items.count()
    return count, qty, total

def _cart_numbers(user):
    order = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
    if not order:
        return 0, 0
    lines = order.items.count()
    qty = order.items.aggregate(q=Sum('quantity'))['q'] or 0
    return lines, qty


def api_cart_summary(request):
    if request.user.is_authenticated:
        count, qty, total = _cart_math(request.user)
    else:
        count, qty, total = sess_summary(request.session)
    return JsonResponse({'count': count, 'qty': qty, 'total': str(total)})

def cart_modal(request):
    """
    Тіло модалки кошика. НЕ login_required — гостям показуємо call-to-action.
    Рендеримо один і той же шаблон _cart_modal_body.html, де є гілки:
      - {# 1) Авторизований #} через змінні order, total
      - {# 2) Гість #} через змінні sitems, total
    """
    if request.user.is_authenticated:
        order, total = _cart_tuple(request.user)
        return render(request, 'zoosvit/orders/_cart_modal_body.html', {'order': order, 'total': total})

    items: List[Dict] = request.session.get(CART_KEY, []) or []
    sitems: List[Dict] = []
    total = Decimal('0')

    for idx, it in enumerate(items):
        kind = it.get('kind')
        obj_id = int(it.get('id'))
        qty = int(it.get('qty', 1))
        price = Decimal(str(it.get('price', '0')))
        line = qty * price

        name = sku = weight = size = ''
        thumb_url = None

        if kind == 'variant':
            v = Product_Variant.objects.select_related('product').filter(pk=obj_id).first()
            if v:
                name = v.product.name
                sku = v.sku or ''
                weight = v.weight or ''
                size = v.size or ''
                thumb_url = (getattr(v, 'image', None) and v.image.url) \
                            or (getattr(v.product, 'image', None) and v.product.image.url)
        else:
            p = Product.objects.filter(pk=obj_id).first()
            if p:
                name = p.name
                thumb_url = getattr(p, 'image', None) and p.image.url

        total += line
        sitems.append({
            'sid': idx,
            'name': name,
            'sku': sku,
            'weight': weight,
            'size': size,
            'qty': qty,
            'line': line,
            'thumb': thumb_url,
        })

    return render(request, 'zoosvit/orders/_cart_modal_body.html', {'sitems': sitems, 'total': total})


def add_variant_to_cart(request, variant_id: int):
    # КРИТИЧНЕ ВИПРАВЛЕННЯ: захист від одночасних запитів
    import time
    user_key = request.user.id if request.user.is_authenticated else request.session.session_key or 'anonymous'
    request_key = f'add_variant_{variant_id}_{user_key}'
    current_time = time.time()
    
    # Перевіряємо кеш запитів (використовуємо сесію для простоти)
    last_request_key = f'last_add_request_{request_key}'
    if last_request_key in request.session:
        last_time = float(request.session[last_request_key])
        time_diff = current_time - last_time
        if time_diff < 2.0:  # менше 2 секунд між запитами
            print(f"ЗАХИСТ PYTHON: Подвійний запит додавання варіанту {variant_id} (різниця: {time_diff:.2f}с) - ігноруємо")
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'message': 'Дуже швидко! Почекайте'}, status=429)
            return redirect('orders:cart')
    
    # Зберігаємо час поточного запиту
    request.session[last_request_key] = current_time
    request.session.modified = True
    
    variant = get_object_or_404(Product_Variant, pk=variant_id)

    if variant.warehouse_quantity is not None and variant.warehouse_quantity <= 0:
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': 'Немає в наявності'}, status=400)
        messages.warning(request, 'Немає в наявності.')
        return redirect('orders:cart')

    if request.user.is_authenticated:
        # КРИТИЧНЕ ВИПРАВЛЕННЯ: спочатку очищаємо проблемні кошики
        ensure_clean_cart(request.user)
        
        # Тепер створюємо або знаходимо чистий кошик
        order, created = Order.objects.get_or_create(
            user=request.user, 
            status=Order.STATUS_CART,
            defaults={
                'status': Order.STATUS_CART,
                'full_name': '',
                'phone': '',
                'email': '',
                'delivery_condition': '',  # ПОРОЖНІ ПОЛЯ!
                'delivery_address': '',
                'comment': ''
            }
        )
        
        # Подвійна перевірка (мало ли що)
        if not created and (order.full_name or order.phone or order.email):
            print(f"КРИТИЧНА ПОМИЛКА: Кошик #{order.id} все ще має дані!")
            order.delete()  # Видаляємо його повністю
            # Створюємо новий чистий кошик
            order = Order.objects.create(
                user=request.user,
                status=Order.STATUS_CART,
                full_name='',
                phone='',
                email='',
                delivery_condition='',  # ПОРОЖНІ ПОЛЯ!
                delivery_address='',
                comment=''
            )
            print(f"   Створено новий чистий кошик #{order.id}")
            
        item, _ = OrderItem.objects.get_or_create(
            order=order, product=variant.product, variant=variant,
            defaults={'retail_price': variant.retail_price, 'quantity': 0}
        )
        new_qty = item.quantity + 1
        if variant.warehouse_quantity is not None and new_qty > variant.warehouse_quantity:
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'message': f'Доступно лише {variant.warehouse_quantity} шт.'}, status=400)
            messages.warning(request, f'Доступно лише {variant.warehouse_quantity} шт.')
            return redirect('orders:cart')

        item.quantity = new_qty
        item.retail_price = variant.retail_price
        item.save(update_fields=['quantity', 'retail_price'])

        if _is_ajax(request):
            count, qty, total = _cart_math(request.user)
            return JsonResponse({'ok': True, 'count': count, 'qty': qty, 'total': str(total)}, status=201)
        messages.success(request, f'Додано: {variant.product.name}')
        return redirect('orders:cart')

    sess_add(request.session, 'variant', variant.id, price=variant.retail_price, inc=1)
    if _is_ajax(request):
        lines, qty, total = sess_summary(request.session)
        return JsonResponse({'ok': True, 'count': lines, 'qty': qty, 'total': str(total)}, status=201)
    return redirect('orders:cart')

def add_to_cart(request, product_id: int):
    variant_id = request.GET.get('variant')
    if variant_id:
        return add_variant_to_cart(request, variant_id)
    
    # КРИТИЧНЕ ВИПРАВЛЕННЯ: захист від одночасних запитів
    import time
    user_key = request.user.id if request.user.is_authenticated else request.session.session_key or 'anonymous'
    request_key = f'add_product_{product_id}_{user_key}'
    current_time = time.time()
    
    # Перевіряємо кеш запитів
    last_request_key = f'last_add_request_{request_key}'
    if last_request_key in request.session:
        last_time = float(request.session[last_request_key])
        time_diff = current_time - last_time
        if time_diff < 2.0:  # менше 2 секунд між запитами
            print(f"ЗАХИСТ PYTHON: Подвійний запит додавання продукту {product_id} (різниця: {time_diff:.2f}с) - ігноруємо")
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'message': 'Дуже швидко! Почекайте'}, status=429)
            return redirect('orders:cart')
    
    # Зберігаємо час поточного запиту
    request.session[last_request_key] = current_time
    request.session.modified = True

    product = get_object_or_404(Product, pk=product_id)

    v = (Product_Variant.objects
         .filter(product=product)
         .order_by('retail_price')
         .filter(warehouse_quantity__gt=0).first()
         or Product_Variant.objects.filter(product=product).order_by('retail_price').first())
    if v:
        return add_variant_to_cart(request, v.id)

    if request.user.is_authenticated:
        # КРИТИЧНЕ ВИПРАВЛЕННЯ: спочатку очищаємо проблемні кошики
        ensure_clean_cart(request.user)
        
        # Тепер створюємо або знаходимо чистий кошик
        order, created = Order.objects.get_or_create(
            user=request.user, 
            status=Order.STATUS_CART,
            defaults={
                'status': Order.STATUS_CART,
                'full_name': '',
                'phone': '',
                'email': '',
                'delivery_condition': '',  # ПОРОЖНІ ПОЛЯ!
                'delivery_address': '',
                'comment': ''
            }
        )
        
        # Подвійна перевірка
        if not created and (order.full_name or order.phone or order.email):
            print(f"КРИТИЧНА ПОМИЛКА: Кошик #{order.id} все ще має дані!")
            order.delete()
            order = Order.objects.create(
                user=request.user,
                status=Order.STATUS_CART,
                full_name='',
                phone='',
                email='',
                delivery_condition='',  # ПОРОЖНІ ПОЛЯ!
                delivery_address='',
                comment=''
            )
            print(f"   Створено новий чистий кошик #{order.id}")
            
        item, _ = OrderItem.objects.get_or_create(
            order=order, product=product, variant=None,
            defaults={'retail_price': product.retail_price, 'quantity': 0}
        )
        item.quantity += 1
        if product.retail_price is not None:
            item.retail_price = product.retail_price
        item.save(update_fields=['quantity', 'retail_price'])

        if _is_ajax(request):
            count, qty, total = _cart_math(request.user)
            return JsonResponse({'ok': True, 'count': count, 'qty': qty, 'total': str(total)}, status=201)
        messages.success(request, f'Додано: {product.name}')
        return redirect('orders:cart')

    price = product.retail_price or Decimal('0')
    sess_add(request.session, 'product', product.id, price=price, inc=1)
    if _is_ajax(request):
        lines, qty, total = sess_summary(request.session)
        return JsonResponse({'ok': True, 'count': lines, 'qty': qty, 'total': str(total)}, status=201)
    return redirect('orders:cart')


@login_required
@require_POST
def item_set_qty(request, item_id):
    order = Order.objects.filter(user=request.user, status=Order.STATUS_CART).first()
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    try:
        qty = int(request.POST.get('qty', '1'))
    except ValueError:
        qty = 1
    if qty < 1:
        qty = 1
    if item.variant and item.variant.warehouse_quantity is not None:
        qty = min(qty, int(item.variant.warehouse_quantity))

    item.quantity = qty
    item.save(update_fields=['quantity'])
    return cart_modal(request)

@login_required
def cart_detail(request):
    # ЗАБОРОНА ПЕРЕХОДУ В КОШИК ЗІ СТОРІНКИ CHECKOUT
    referer = request.META.get('HTTP_REFERER', '')
    if '/checkout/' in referer:
        print(f"ЗАБОРОНА: Перехід в кошик зі сторінки checkout")
        messages.warning(request, 'Перейдіть на сторінку оформлення замовлення')
        return redirect('orders:checkout')
    
    order, total = _cart_tuple(request.user)
    return render(request, 'zoosvit/orders/cart.html', {'order': order, 'total': total})

@login_required
def checkout(request):
    # ВАЖЛИВО: шукаємо ТІЛЬКИ кошикові замовлення
    order = get_object_or_404(Order, user=request.user, status=Order.STATUS_CART)
    
    # Перевіряємо, чи є товари в кошику
    if not order.items.exists():
        messages.warning(request, 'Кошик порожній')
        return redirect('orders:cart')
    
    # РАДИКАЛЬНЕ ВИПРАВЛЕННЯ: очищаємо ВСІ можливі джерела повідомлень
    if request.method == 'GET':
        # Очищаємо Django messages
        from django.contrib.messages import get_messages
        storage = get_messages(request)
        list(storage)  # Читаємо всі повідомлення щоб очистити
        
        # Очищаємо сесію від можливих повідомлень
        if 'order_success' in request.session:
            del request.session['order_success']
        if 'checkout_message' in request.session:
            del request.session['checkout_message']
        if '_messages' in request.session:
            del request.session['_messages']
        request.session.modified = True
        
        # FORCE ОЧИСТКА: видаляємо всі messages з бази якщо вони там
        from django.contrib.messages.storage.base import Message
        try:
            # Очищаємо всі можливі залишки
            storage._queued_messages = []
            storage.added_new = False
        except:
            pass
            
        print(f"FORCE ОЧИСТКА: Всі повідомлення очищено для користувача {request.user.username}")
        
        # Додаткова перевірка: якщо замовлення має заповнені контакти - очищаємо їх
        if order.full_name or order.phone or order.email:
            print(f"КРИТИЧНА ПОМИЛКА: Кошик #{order.id} має заповнені дані!")
            print(f"   Повідомлення про 'successfully оформлено' може показатися через це")
            order.full_name = ''
            order.phone = ''
            order.email = ''
            order.delivery_condition = ''
            order.delivery_address = ''
            order.comment = ''
            order.delivery_condition = ''
            order.save()
            print(f"   Очищено всі контактні дані")
    
    # Перевіряємо, чи це нове кошикове замовлення (без контактних даних)
    is_new_order = not (order.full_name or order.phone or order.email)
    
    # Дебаг: логуємо інформацію
    print(f"DEBUG CHECKOUT: order_id={order.id}, status={order.status}, is_new={is_new_order}")
    print(f"DEBUG CHECKOUT: full_name='{order.full_name}', phone='{order.phone}', email='{order.email}'")
    
    if request.method == 'POST':
        form = OrderCheckoutForm(request.POST)
        if form.is_valid():
            # ТІЛЬКИ ТЕПЕР оновлюємо існуюче замовлення
            order.full_name = form.cleaned_data['full_name']
            order.phone = form.cleaned_data['phone']
            order.email = form.cleaned_data['email']
            order.city = form.cleaned_data['city']
            order.delivery_address = form.cleaned_data['delivery_address']
            order.comment = form.cleaned_data.get('comment', '')
            
            # Дані Нової Пошти (якщо вибрано Нова Пошта)
            delivery_type = form.cleaned_data['delivery_type']
            if delivery_type == 'nova_poshta':
                order.delivery_condition = 'nova_poshta'
                # city_ref та warehouse_ref будуть заповнені через JavaScript
                order.city_ref = request.POST.get('city_ref', '')
                order.warehouse_ref = request.POST.get('warehouse_ref', '')
            else:
                order.delivery_condition = 'ukrposhta'
            
            # Обробка способу оплати
            payment_method = form.cleaned_data.get('payment_method', 'cash')
            order.payment_method = payment_method
            
            # Якщо оплата карткою - saletype = '2', інакше '1'
            if payment_method == 'card_online':
                order.sale_type = '2'
            else:
                order.sale_type = '1'
            
            # Встановлюємо статус "в обробці"
            order.status = Order.STATUS_IN_PROCESS
            order.save()
            
            # Генеруємо номер замовлення
            order_number = order.order_number or order.id
            print(f"DEBUG: Оформлено замовлення #{order_number}, новий статус: {order.status}")
            
            # АВТОМАТИЧНЕ СТВОРЕННЯ ТТН ДЛЯ НОВОЇ ПОШТИ
            if delivery_type == 'nova_poshta' and order.city_ref and order.warehouse_ref:
                print(f"📦 Автоматичне створення ТТН для замовлення #{order_number}")
                
                # Перевіряємо налаштування відправника
                if all([
                    settings.NOVA_POSHTA_SENDER_REF,
                    settings.NOVA_POSHTA_SENDER_CONTACT_REF,
                    settings.NOVA_POSHTA_SENDER_ADDRESS_REF,
                    settings.NOVA_POSHTA_SENDER_CITY_REF
                ]):
                    try:
                        total_amount = order.total_amount
                        
                        # ДЛЯ ДЕБАГУ: завжди NonCash (без післяплати)
                        payment_method_api = 'NonCash'
                        backward_delivery = None  # Вимикаємо післяплату
                        
                        send_date = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
                        
                        print(f"🔍 DEBUG ТТН: payment={payment_method}, api_method={payment_method_api}, backward={backward_delivery}")
                        
                        order_data = {
                            'sender_ref': settings.NOVA_POSHTA_SENDER_REF,
                            'sender_contact_ref': settings.NOVA_POSHTA_SENDER_CONTACT_REF,
                            'sender_address_ref': settings.NOVA_POSHTA_SENDER_ADDRESS_REF,
                            'sender_city_ref': settings.NOVA_POSHTA_SENDER_CITY_REF,
                            'sender_phone': settings.NOVA_POSHTA_SENDER_PHONE,
                            
                            'recipient_name': order.full_name,
                            'recipient_phone': order.phone,
                            'recipient_city_ref': order.city_ref,
                            'recipient_warehouse_ref': order.warehouse_ref,
                            
                            'cost': float(total_amount),
                            'weight': '1',
                            'seats_amount': '1',
                            'description': f'Замовлення #{order_number}',
                            'payment_method': payment_method_api,
                            'backward_delivery_money': backward_delivery,
                            'date': send_date
                        }
                        
                        result = nova_poshta_api.create_internet_document(order_data)
                        
                        if result:
                            order.novaposhta_ttn = result.get('int_doc_number', '')
                            order.save(update_fields=['novaposhta_ttn'])
                            print(f"✅ ТТН створено: {order.novaposhta_ttn}")
                            # messages.success(request, f'ТТН Нової Пошти створено: {order.novaposhta_ttn}')
                        else:
                            print(f"❌ Не вдалося створити ТТН")
#                             messages.warning(request, 'Замовлення оформлено, але ТТН не створено. Зверніться до менеджера.')
                    except Exception as e:
                        print(f"❌ Помилка створення ТТН: {e}")
#                         messages.warning(request, 'Замовлення оформлено, але виникла помилка при створенні ТТН.')
                else:
                    print("⚠️ Дані відправника не налаштовані")
                    messages.info(request, 'Замовлення оформлено. ТТН буде створено менеджером.')
            
            # Якщо оплата карткою - перенаправляємо на оплату
            if payment_method == 'card_online':
                return redirect('orders:payment', order_id=order.id)
            
            # Готівка - одразу в список замовлень
            return redirect('orders:list')
    else:
        # Просто показуємо порожню форму - НЕ ЗБЕРІГАЄМО НІЧОГО
        if is_new_order:
            # НЕ ПІДСТАВЛЯЄМО USERNAME - залишаємо ПІБ порожнім!
            initial = {
                'email': request.user.email or '',
                'delivery_type': 'nova_poshta'
            }
        else:
            if order.delivery_condition == 'nova_poshta':
                current_delivery_type = 'nova_poshta'
            elif order.delivery_condition == 'ukrposhta':
                current_delivery_type = 'ukrposhta'
            else:
                current_delivery_type = 'nova_poshta'
                
            initial = {
                'full_name': order.full_name or '',  # НЕ підставляємо username!
                'phone': order.phone,
                'email': order.email or request.user.email or '',
                'delivery_type': current_delivery_type,
                'delivery_address': order.delivery_address,
                'comment': order.comment,
            }
        
        form = OrderCheckoutForm(initial=initial)
    
    return render(request, 'zoosvit/orders/checkout.html', {'order': order, 'form': form})

@login_required
def orders_list(request):
    qs = Order.objects.filter(user=request.user).exclude(status=Order.STATUS_CART)
    return render(request, 'orders/history.html', {'orders': qs})

@login_required
def order_list(request):
    orders = request.user.orders.all()
    return render(request, 'zoosvit/orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'zoosvit/orders/order_detail.html', {'order': order})


def _sess_get_items(request):
    return list(request.session.get(CART_KEY, []) or [])

def _sess_save_items(request, items):
    request.session[CART_KEY] = items
    request.session.modified = True

def cart_item_inc(request, item_id: int):
    # ПОКРАЩЕНИЙ ЗАХИСТ ВІД ПОДВІЙНИХ КЛІКІВ
    session_key = f'cart_inc_{item_id}_{request.user.id if request.user.is_authenticated else "guest"}'
    import time
    current_time = time.time()
    
    # Перевіряємо чи був клік недавно
    if session_key in request.session:
        last_click = float(request.session[session_key])
        time_diff = current_time - last_click
        if time_diff < 2:  # ЗБІЛЬШУЄМО ЧАС ДО 2 СЕКУНД!
            print(f"ЗАХИСТ: Подвійний клік на товар {item_id} (різниця: {time_diff:.2f}с) - ігноруємо")
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'message': 'Дуже швидко! Почекайте'}, status=429)
            return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')
    
    # Зберігаємо час кліка
    request.session[session_key] = current_time
    request.session.modified = True
    
    print(f"ДОДАЄМО ТОВАР: item_id={item_id}, user={request.user.username if request.user.is_authenticated else 'guest'}")
    if request.user.is_authenticated and not request.GET.get('guest'):
        item = get_object_or_404(
            OrderItem, id=item_id,
            order__user=request.user, order__status=Order.STATUS_CART
        )
        if item.variant and item.variant.warehouse_quantity is not None \
           and item.quantity + 1 > item.variant.warehouse_quantity:
            return JsonResponse({'ok': False, 'message': 'Перевищено доступний склад'}, status=400) if _is_ajax(request) \
                   else redirect('orders:cart')
        item.quantity += 1
        item.save(update_fields=['quantity'])
    else:
        sid = int(item_id)
        items = _sess_get_items(request)
        if 0 <= sid < len(items):
            items[sid]['qty'] = int(items[sid].get('qty', 1)) + 1
            _sess_save_items(request, items)
    return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')

def cart_item_dec(request, item_id: int):
    # ПОКРАЩЕНИЙ ЗАХИСТ ВІД ПОДВІЙНИХ КЛІКІВ
    session_key = f'cart_dec_{item_id}_{request.user.id if request.user.is_authenticated else "guest"}'
    import time
    current_time = time.time()
    
    # Перевіряємо чи був клік недавно
    if session_key in request.session:
        last_click = float(request.session[session_key])
        time_diff = current_time - last_click
        if time_diff < 2:  # ЗБІЛЬШУЄМО ЧАС ДО 2 СЕКУНД!
            print(f"ЗАХИСТ: Подвійний клік на товар {item_id} (різниця: {time_diff:.2f}с) - ігноруємо")
            if _is_ajax(request):
                return JsonResponse({'ok': False, 'message': 'Дуже швидко! Почекайте'}, status=429)
            return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')
    
    # Зберігаємо час кліка
    request.session[session_key] = current_time
    request.session.modified = True
    
    print(f"ВІДНІМАЄМО ТОВАР: item_id={item_id}, user={request.user.username if request.user.is_authenticated else 'guest'}")
    if request.user.is_authenticated and not request.GET.get('guest'):
        item = get_object_or_404(
            OrderItem, id=item_id,
            order__user=request.user, order__status=Order.STATUS_CART
        )
        if item.quantity > 1:
            item.quantity -= 1
            item.save(update_fields=['quantity'])
        else:
            item.delete()
    else:
        sid = int(item_id)
        items = _sess_get_items(request)
        if 0 <= sid < len(items):
            q = int(items[sid].get('qty', 1)) - 1
            if q <= 0:
                items.pop(sid)
            else:
                items[sid]['qty'] = q
            _sess_save_items(request, items)
    return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')

def cart_item_remove(request, item_id: int):
    if request.user.is_authenticated and not request.GET.get('guest'):
        item = get_object_or_404(
            OrderItem, id=item_id,
            order__user=request.user, order__status=Order.STATUS_CART
        )
        item.delete()
    else:
        sid = int(item_id)
        items = _sess_get_items(request)
        if 0 <= sid < len(items):
            items.pop(sid)
            _sess_save_items(request, items)
    return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')

def cart_clear(request):
    try:
        if request.user.is_authenticated and not request.GET.get('guest'):
            try:
                user = request.user
                if user.is_authenticated:
                    order = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
                    if order:
                        print(f"Очищаємо кошик: видаляємо замовлення #{order.id}")
                        order.delete()
                    else:
                        print("Кошик вже порожній")
                else:
                    print("Користувач не авторизований")
            except Exception as db_error:
                print(f"Помилка бази даних при очищенні кошика: {db_error}")
                _sess_save_items(request, [])
        else:
            _sess_save_items(request, [])
    except Exception as e:
        print(f"Критична помилка при очищенні кошика: {e}")
        try:
            _sess_save_items(request, [])
        except:
            pass
    
    return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')


# ========================================
# API для Нової Пошти
# ========================================

def api_search_cities(request):
    """
    API для пошуку міст Нової Пошти
    GET /orders/api/cities/?query=київ
    """
    query = request.GET.get('query', '').strip()
    
    # DEBUG: Логуємо запит
    print(f"🔍 DEBUG: Пошук міст, query='{query}'")
    print(f"🔑 DEBUG: API key = {settings.NOVA_POSHTA_API_KEY[:20]}...")
    
    if len(query) < 2:
        print("❌ DEBUG: Запит занадто короткий")
        return JsonResponse({'cities': []}, safe=False)
    
    cities = nova_poshta_api.search_cities(query)
    
    print(f"🏛️ DEBUG: Знайдено міст: {len(cities) if cities else 0}")
    
    if cities is None:
        print("❌ DEBUG: Помилка API")
        return JsonResponse({'error': 'Помилка підключення до API Нової Пошти'}, status=500)
    
    return JsonResponse({'cities': cities}, safe=False)


def api_get_warehouses(request):
    """
    API для отримання відділень Нової Пошти
    GET /orders/api/warehouses/?city_ref=XXX
    """
    city_ref = request.GET.get('city_ref', '').strip()
    
    if not city_ref:
        return JsonResponse({'error': 'Не вказано Ref міста'}, status=400)
    
    warehouses = nova_poshta_api.get_warehouses(city_ref)
    
    if warehouses is None:
        return JsonResponse({'error': 'Помилка підключення до API Нової Пошти'}, status=500)
    
    return JsonResponse({'warehouses': warehouses}, safe=False)


@login_required
def create_novaposhta_shipment(request, order_id):
    """
    Створення відправлення в Новій Пошті для замовлення
    """
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    
    # Перевіряємо що замовлення оформлене і доставка через Нову Пошту
    if order.status == Order.STATUS_CART:
        return JsonResponse({'error': 'Замовлення не оформлене'}, status=400)
    
    if order.delivery_condition != 'nova_poshta':
        return JsonResponse({'error': 'Доставка не через Нову Пошту'}, status=400)
    
    # Перевіряємо чи вже створено ТТН
    if order.novaposhta_ttn:
        return JsonResponse({'ttn': order.novaposhta_ttn, 'message': 'ТТН вже створено'})
    
    # Перевіряємо налаштування відправника
    if not all([
        settings.NOVA_POSHTA_SENDER_REF,
        settings.NOVA_POSHTA_SENDER_CONTACT_REF,
        settings.NOVA_POSHTA_SENDER_ADDRESS_REF,
        settings.NOVA_POSHTA_SENDER_CITY_REF
    ]):
        return JsonResponse({
            'error': 'Не налаштовані дані відправника. Зверніться до адміністратора.'
        }, status=500)
    
    # Підготовка даних для створення накладної
    total_amount = order.total_amount
    
    # Визначаємо спосіб оплати для API Нової Пошти
    payment_method_api = 'NonCash' if order.payment_method == 'card_online' else 'Cash'
    backward_delivery = None
    
    if order.payment_method == 'cash':
        backward_delivery = float(total_amount)  # Накладений платіж
    
    # Дата відправки - завтра
    send_date = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
    
    order_data = {
        'sender_ref': settings.NOVA_POSHTA_SENDER_REF,
        'sender_contact_ref': settings.NOVA_POSHTA_SENDER_CONTACT_REF,
        'sender_address_ref': settings.NOVA_POSHTA_SENDER_ADDRESS_REF,
        'sender_city_ref': settings.NOVA_POSHTA_SENDER_CITY_REF,
        'sender_phone': settings.NOVA_POSHTA_SENDER_PHONE,
        
        'recipient_name': order.full_name,
        'recipient_phone': order.phone,
        'recipient_city_ref': order.city_ref,
        'recipient_warehouse_ref': order.warehouse_ref,
        
        'cost': float(total_amount),
        'weight': '1',  # Вага за замовчуванням 1 кг
        'seats_amount': '1',  # Кількість місць
        'description': f'Замовлення #{order.order_number or order.id}',
        'payment_method': payment_method_api,
        'backward_delivery_money': backward_delivery,
        'date': send_date
    }
    
    # Створюємо накладну
    result = nova_poshta_api.create_internet_document(order_data)
    
    if result:
        # Зберігаємо ТТН в замовлення
        order.novaposhta_ttn = result.get('int_doc_number', '')
        order.save(update_fields=['novaposhta_ttn'])
        
        return JsonResponse({
            'success': True,
            'ttn': result.get('int_doc_number'),
            'message': f'ТТН створено: {result.get("int_doc_number")}'
        })
    else:
        return JsonResponse({
            'error': 'Не вдалося створити накладну. Перевірте налаштування API.'
        }, status=500)
