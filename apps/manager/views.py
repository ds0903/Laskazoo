from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
import json

from apps.users.models import CustomUser
from apps.orders.models import Order, OrderItem
from apps.ts_ftps.models import TSGoods
from apps.products.models import Product, Category, Main_Categories, Brand


def is_manager(user):
    """Перевірка чи користувач є менеджером"""
    return user.is_staff or user.groups.filter(name='Менеджер').exists()


@login_required
def manager_dashboard(request):
    """Головна сторінка кабінету менеджера"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    # Статистика для дашборду
    total_users = CustomUser.objects.count()
    total_orders = Order.objects.exclude(status='cart').count()
    pending_orders = Order.objects.filter(status__in=['new', 'in_process']).count()
    total_products = Product.objects.filter(is_active=True).count()
    
    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_products': total_products,
    }
    
    return render(request, 'manager/dashboard.html', context)


@login_required
def manager_users(request):
    """Перегляд списку користувачів"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    # Пошук
    search_query = request.GET.get('search', '')
    users = CustomUser.objects.all().order_by('-date_joined')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    # Пагінація
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'manager/users.html', context)


@login_required
def manager_orders(request):
    """Перегляд списку замовлень"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    # Фільтрація за статусом
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    orders = Order.objects.exclude(status='cart').select_related('user').prefetch_related('items').order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Пагінація
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'manager/orders.html', context)


@login_required
def manager_order_detail(request, order_id):
    """Детальна інформація про замовлення"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    order = get_object_or_404(Order.objects.prefetch_related('items__product', 'items__variant'), id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Статус замовлення змінено на "{order.get_status_display()}"')
            return redirect('manager:order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'manager/order_detail.html', context)


@login_required
def manager_import_products(request):
    """Імпорт товарів з TSGoods"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    context = {}
    return render(request, 'manager/import_products.html', context)


@login_required
def search_ts_goods(request):
    """AJAX пошук товарів у TSGoods"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    search_query = request.GET.get('q', '').strip()
    
    if not search_query or len(search_query) < 2:
        return JsonResponse({'results': []})
    
    # Пошук за штрих-кодом, артикулом або назвою
    goods = TSGoods.objects.filter(
        Q(barcode__icontains=search_query) |
        Q(articul__icontains=search_query) |
        Q(good_name__icontains=search_query)
    )[:50]
    
    results = []
    for good in goods:
        results.append({
            'id': good.good_id,
            'name': good.good_name or '',
            'articul': good.articul or '',
            'barcode': good.barcode or '',
            'price': float(good.equal_sale_price) if good.equal_sale_price else 0,
            'quantity': float(good.warehouse_quantity) if good.warehouse_quantity else 0,
        })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["POST"])
def create_products_from_ts(request):
    """Створення товарів на основі вибраних з TSGoods"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        data = json.loads(request.body)
        selected_goods = data.get('goods', [])
        
        if not selected_goods:
            return JsonResponse({'error': 'Не вибрано товарів'}, status=400)
        
        created_products = []
        errors = []
        
        for item in selected_goods:
            good_id = item.get('good_id')
            category_id = item.get('category_id')
            brand_id = item.get('brand_id')
            image_url = item.get('image_url')
            
            if not good_id or not category_id or not brand_id:
                errors.append(f"Товар {good_id}: не вказана категорія або бренд")
                continue
            
            try:
                ts_good = TSGoods.objects.get(good_id=good_id)
                category = Category.objects.get(id=category_id)
                brand = Brand.objects.get(id=brand_id)
                
                # Перевіряємо чи вже існує товар з таким torgsoft_id
                if Product.objects.filter(torgsoft_id=good_id).exists():
                    errors.append(f"Товар {ts_good.good_name} вже існує")
                    continue
                
                # Створюємо новий товар
                product = Product(
                    torgsoft_id=good_id,
                    barcode=ts_good.barcode,
                    name=ts_good.good_name,
                    sku=ts_good.articul,
                    category=category,
                    brand=brand,
                    description=ts_good.description or ts_good.new_description or '',
                    retail_price=ts_good.equal_sale_price or 0,
                    retail_price_with_discount=ts_good.equal_sale_price or 0,
                    warehouse_quantity=int(ts_good.warehouse_quantity) if ts_good.warehouse_quantity else 0,
                    is_active=True,
                )
                
                # TODO: Обробка завантаження зображення з image_url
                # Якщо потрібно завантажити фото, додайте логіку тут
                
                product.save()
                created_products.append({
                    'id': product.id,
                    'name': product.name,
                    'slug': product.slug,
                })
                
            except TSGoods.DoesNotExist:
                errors.append(f"Товар {good_id} не знайдено в TSGoods")
            except Category.DoesNotExist:
                errors.append(f"Категорія {category_id} не знайдена")
            except Brand.DoesNotExist:
                errors.append(f"Бренд {brand_id} не знайдений")
            except Exception as e:
                errors.append(f"Помилка створення товару {good_id}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'created': len(created_products),
            'products': created_products,
            'errors': errors,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невірний формат даних'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_categories_and_brands(request):
    """API для отримання списку категорій та брендів"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    main_categories = []
    for main_cat in Main_Categories.objects.filter(is_active=True).prefetch_related('categories'):
        categories = []
        for cat in main_cat.categories.filter(is_active=True):
            categories.append({
                'id': cat.id,
                'name': cat.name,
            })
        
        main_categories.append({
            'id': main_cat.id,
            'name': main_cat.name,
            'categories': categories,
        })
    
    brands = [
        {'id': brand.id, 'name': brand.name}
        for brand in Brand.objects.filter(is_active=True).order_by('name')
    ]
    
    return JsonResponse({
        'main_categories': main_categories,
        'brands': brands,
    })
