from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.core.management import call_command
import json

from apps.users.models import CustomUser
from apps.orders.models import Order, OrderItem
from apps.ts_ftps.models import TSGoods
from apps.products.models import Product, Category, Main_Categories, Brand, PopularProduct, PopularCategory
from apps.manager.models import Banner


def is_manager(user):
    """Перевірка чи користувач є менеджером"""
    return user.is_staff or user.groups.filter(name='Менеджер').exists()


@login_required
def manager_dashboard(request):
    """Головна сторінка кабінету менеджера"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
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
    """AJAX пошук товарів у TSGoods за штрихкодом"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    search_query = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    
    existing_torgsoft_ids = set(
        Product.objects.filter(torgsoft_id__isnull=False)
        .values_list('torgsoft_id', flat=True)
    )
    
    goods_query = TSGoods.objects.exclude(good_id__in=existing_torgsoft_ids)
    
    if search_query:
        goods_query = goods_query.filter(barcode__icontains=search_query)
    
    paginator = Paginator(goods_query.order_by('-created_at'), 10)
    page_obj = paginator.get_page(page)
    
    results = []
    for good in page_obj:
        results.append({
            'id': good.good_id,
            'name': good.good_name or '',
            'articul': good.articul or '',
            'barcode': good.barcode or '',
            'price': float(good.wholesale_price) if good.wholesale_price else 0,
            'quantity': float(good.warehouse_quantity) if good.warehouse_quantity else 0,
        })
    
    return JsonResponse({
        'results': results,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count,
    })


@login_required
@require_http_methods(["POST"])
def sync_ts_goods(request):
    """Синхронізація товарів з сервера"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        call_command('import_tsgoods')
        
        return JsonResponse({
            'success': True,
            'message': 'Синхронізацію завершено успішно!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Помилка синхронізації: {str(e)}'
        }, status=500)


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
            
            if not good_id or not category_id or not brand_id:
                errors.append(f"Товар {good_id}: не вказана категорія або бренд")
                continue
            
            try:
                ts_good = TSGoods.objects.get(good_id=good_id)
                category = Category.objects.get(id=category_id)
                brand = Brand.objects.get(id=brand_id)
                
                if Product.objects.filter(torgsoft_id=good_id).exists():
                    errors.append(f"Товар {ts_good.good_name} вже існує")
                    continue
                
                product = Product(
                    torgsoft_id=good_id,
                    barcode=ts_good.barcode,
                    name=ts_good.good_name,
                    sku=ts_good.articul,
                    category=category,
                    brand=brand,
                    description=ts_good.new_description or '',
                    retail_price=ts_good.equal_sale_price or 0,
                    retail_price_with_discount=ts_good.equal_sale_price or 0,
                    warehouse_quantity=int(ts_good.warehouse_quantity) if ts_good.warehouse_quantity else 0,
                    is_active=True,
                )
                
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


@login_required
def manager_products(request):
    """Перегляд всіх товарів на сайті з фільтрами"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    products = Product.objects.select_related('category', 'category__main_category', 'brand').all()
    
    search_query = request.GET.get('search', '').strip()
    main_category_id = request.GET.get('main_category', '')
    category_id = request.GET.get('category', '')
    brand_id = request.GET.get('brand', '')
    is_active = request.GET.get('is_active', '')
    in_stock = request.GET.get('in_stock', '')
    sort_by = request.GET.get('sort', '-id')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(torgsoft_id__icontains=search_query)
        )
    
    if main_category_id:
        products = products.filter(category__main_category_id=main_category_id)
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    if is_active:
        products = products.filter(is_active=is_active == 'true')
    
    if in_stock == 'yes':
        products = products.filter(warehouse_quantity__gt=0)
    elif in_stock == 'no':
        products = products.filter(warehouse_quantity=0)
    
    if sort_by:
        products = products.order_by(sort_by)
    
    total_products = products.count()
    active_products = products.filter(is_active=True).count()
    in_stock_products = products.filter(warehouse_quantity__gt=0).count()
    
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    main_categories = Main_Categories.objects.filter(is_active=True).order_by('name')
    categories = Category.objects.filter(is_active=True).select_related('main_category').order_by('name')
    brands = Brand.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'main_category_id': main_category_id,
        'category_id': category_id,
        'brand_id': brand_id,
        'is_active': is_active,
        'in_stock': in_stock,
        'sort_by': sort_by,
        'total_products': total_products,
        'active_products': active_products,
        'in_stock_products': in_stock_products,
        'main_categories': main_categories,
        'categories': categories,
        'brands': brands,
    }
    
    return render(request, 'manager/products.html', context)


@login_required
@require_http_methods(["POST"])
def update_product_status(request, product_id):
    """Зміна статусу товару"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body)
        new_status = data.get('is_active')
        
        if new_status is not None:
            product.is_active = new_status
            product.save()
            
            status_text = 'Активний' if new_status else 'Неактивний'
            return JsonResponse({
                'success': True,
                'message': f'Статус товару змінено на "{status_text}"',
                'is_active': product.is_active
            })
        else:
            return JsonResponse({'error': 'Не вказано статус'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невірний формат даних'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def manager_banners(request):
    """Керування банерами"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    banners = Banner.objects.all().order_by('position', '-created_at')
    
    context = {
        'banners': banners,
    }
    
    return render(request, 'manager/banners.html', context)


@login_required
@require_http_methods(["POST"])
def banner_add(request):
    """Додавання нового банера"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        title = request.POST.get('title', '')
        link = request.POST.get('link', '')
        position = int(request.POST.get('position', 0))
        image = request.FILES.get('image')
        
        if not image:
            return JsonResponse({'error': 'Зображення обов\'язкове'}, status=400)
        
        banner = Banner.objects.create(
            title=title,
            link=link,
            position=position,
            image=image,
            is_active=True
        )
        
        messages.success(request, f'Банер "{banner.title or banner.id}" успішно додано!')
        return JsonResponse({'success': True, 'banner_id': banner.id})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def banner_update(request, banner_id):
    """Оновлення банера"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        banner = get_object_or_404(Banner, id=banner_id)
        
        banner.title = request.POST.get('title', banner.title)
        banner.link = request.POST.get('link', banner.link)
        banner.position = int(request.POST.get('position', banner.position))
        
        if 'image' in request.FILES:
            banner.image = request.FILES['image']
        
        if 'is_active' in request.POST:
            banner.is_active = request.POST.get('is_active') == 'true'
        
        banner.save()
        
        messages.success(request, f'Банер оновлено!')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def banner_delete(request, banner_id):
    """Видалення банера"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        banner = get_object_or_404(Banner, id=banner_id)
        banner.delete()
        
        messages.success(request, 'Банер видалено!')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def manager_popular_products(request):
    """Керування популярними товарами"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    popular_products = PopularProduct.objects.select_related('product').order_by('position', '-created_at')
    
    # ВИПРАВЛЕНО: Показуємо ВСІ активні товари, без обмеження
    all_products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'popular_products': popular_products,
        'all_products': all_products,
    }
    
    return render(request, 'manager/popular_products.html', context)


@login_required
def search_products_ajax(request):
    """AJAX пошук товарів для додавання в хіти"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    # Шукаємо по назві, артикулу та штрихкоду
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(sku__icontains=query) |
        Q(barcode__icontains=query),
        is_active=True
    ).values('id', 'name', 'barcode', 'sku')[:50]  # Обмежуємо до 50 результатів
    
    return JsonResponse({'products': list(products)})


@login_required
@require_http_methods(["POST"])
def popular_product_add(request):
    """Додавання товару в популярні"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        product_id = request.POST.get('product_id')
        position = int(request.POST.get('position', 0))
        
        product = get_object_or_404(Product, id=product_id)
        
        if PopularProduct.objects.filter(product=product).exists():
            return JsonResponse({'error': 'Цей товар вже в популярних'}, status=400)
        
        popular = PopularProduct.objects.create(
            product=product,
            position=position,
            is_active=True
        )
        
        messages.success(request, f'Товар "{product.name}" додано в популярні!')
        return JsonResponse({'success': True, 'id': popular.id})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def popular_product_update(request, popular_id):
    """Оновлення популярного товару"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        popular = get_object_or_404(PopularProduct, id=popular_id)
        
        if 'is_active' in request.POST:
            popular.is_active = request.POST.get('is_active') == 'true'
        
        popular.save()
        
        messages.success(request, 'Популярний товар оновлено!')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def popular_product_delete(request, popular_id):
    """Видалення з популярних товарів"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        popular = get_object_or_404(PopularProduct, id=popular_id)
        popular.delete()
        
        messages.success(request, 'Товар видалено з популярних!')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def manager_popular_categories(request):
    """Керування популярними категоріями"""
    if not is_manager(request.user):
        messages.error(request, 'У вас немає доступу до кабінету менеджера')
        return redirect('home')
    
    popular_categories = PopularCategory.objects.select_related('category__main_category').order_by('position', '-created_at')
    all_categories = Category.objects.filter(is_active=True).select_related('main_category').order_by('name')
    
    context = {
        'popular_categories': popular_categories,
        'all_categories': all_categories,
    }
    
    return render(request, 'manager/popular_categories.html', context)


@login_required
@require_http_methods(["POST"])
def popular_category_add(request):
    """Додавання категорії в популярні"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        category_id = request.POST.get('category_id')
        position = int(request.POST.get('position', 0))
        
        category = get_object_or_404(Category, id=category_id)
        
        if PopularCategory.objects.filter(category=category).exists():
            return JsonResponse({'error': 'Ця категорія вже в популярних'}, status=400)
        
        popular = PopularCategory.objects.create(
            category=category,
            position=position,
            is_active=True
        )
        
        messages.success(request, f'Категорію "{category.name}" додано в популярні!')
        return JsonResponse({'success': True, 'id': popular.id})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def popular_category_update(request, popular_id):
    """Оновлення популярної категорії"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        popular = get_object_or_404(PopularCategory, id=popular_id)
        
        popular.position = int(request.POST.get('position', popular.position))
        
        if 'is_active' in request.POST:
            popular.is_active = request.POST.get('is_active') == 'true'
        
        popular.save()
        
        messages.success(request, 'Популярну категорію оновлено!')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def popular_category_delete(request, popular_id):
    """Видалення з популярних категорій"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        popular = get_object_or_404(PopularCategory, id=popular_id)
        popular.delete()
        
        messages.success(request, 'Категорію видалено з популярних!')
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def reorder_banners(request):
    """Зміна порядку банерів"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        data = json.loads(request.body)
        order = data.get('order', [])
        
        for item in order:
            banner_id = item.get('id')
            position = item.get('position')
            
            Banner.objects.filter(id=banner_id).update(position=position)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def reorder_popular_products(request):
    """Зміна порядку популярних товарів"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        data = json.loads(request.body)
        order = data.get('order', [])
        
        for item in order:
            popular_id = item.get('id')
            position = item.get('position')
            
            PopularProduct.objects.filter(id=popular_id).update(position=position)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def reorder_popular_categories(request):
    """Зміна порядку популярних категорій"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    try:
        data = json.loads(request.body)
        order = data.get('order', [])
        
        for item in order:
            popular_id = item.get('id')
            position = item.get('position')
            
            PopularCategory.objects.filter(id=popular_id).update(position=position)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_categories_by_main(request):
    """API для отримання категорій по головній категорії (каскадний вибір)"""
    if not is_manager(request.user):
        return JsonResponse({'error': 'Немає доступу'}, status=403)
    
    main_category_id = request.GET.get('main_category_id')
    
    if not main_category_id:
        return JsonResponse({'categories': []})
    
    categories = Category.objects.filter(
        main_category_id=main_category_id,
        is_active=True
    ).values('id', 'name').order_by('name')
    
    return JsonResponse({'categories': list(categories)})
