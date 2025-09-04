# apps/products/views.py
from django.shortcuts import render, get_object_or_404
from .models import Main_Categories, Category, Product, Brand, Product_Variant
from django.db.models import Count, Q, Prefetch

try:
    from apps.favourites.models import Favourite
except Exception:
    Favourite = None

def catalog(request):
    mains = Main_Categories.objects.all()

    variants_qs = (
        Product_Variant.objects
        .only('id', 'product_id', 'sku', 'retail_price', 'weight', 'size', 'image', 'warehouse_quantity')
        .order_by('retail_price')   # або як тобі треба
    )

    base_qs = (
        Product.objects
        .select_related('brand', 'category')
        .prefetch_related(
            Prefetch('variants', queryset=variants_qs, to_attr='variants_for_card')
        )
    )

    products, filt_ctx = _apply_filters(request, base_qs)

    if request.user.is_authenticated:
        fav_variant_ids = list(
            Favourite.objects
            .filter(user=request.user, variant__isnull=False)
            .values_list('variant_id', flat=True)
        )
    else:
        fav_variant_ids = list(map(int, request.session.get('fav_variant_ids', [])))

    ctx = {
        'title':    'Каталог',
        'mains':    mains,
        'products': products,   # уже має product.variants_for_card
        'fav_variant_ids':  list(fav_variant_ids),
        **filt_ctx,
    }
    return render(request, 'zoosvit/products/catalog.html', ctx)

def subcategory_list(request, main_slug):
    main = get_object_or_404(Main_Categories, slug=main_slug)
    subs = main.categories.all()
    return render(request, 'zoosvit/products/subcategory_list.html', {
        'main':       main,
        'categories': subs,
    })

def category_list(request, main_slug, slug):
    category = get_object_or_404(
        Category,
        slug=slug,
        main_category__slug=main_slug
    )

    # базовий QS — тільки товари цієї категорії
    base_qs = (
        Product.objects
        .filter(category=category)
        .select_related('brand', 'category')
        .prefetch_related('variants')
    )

    # ⬇️ головне — застосувати ті самі фільтри, що й у каталозі
    products, filt_ctx = _apply_filters(request, base_qs)

    return render(request, 'zoosvit/products/category_list.html', {
        'main':     category.main_category,
        'category': category,
        'products': products,
        **filt_ctx,                 # brands, price_min, price_max, in_stock, selected_brands
    })

def product_detail(request, main_slug, slug, product_slug):
    # 1) перевіряємо, що категорія належить до головної
    category = get_object_or_404(
        Category,
        slug=slug,
        main_category__slug=main_slug
    )
    # 2) тягнемо сам товар
    product = get_object_or_404(
        Product,
        slug=product_slug,
        category=category
    )

    variants = product.variants.all()

    return render(request, 'zoosvit/products/product_detail.html', {
        'main_slug': main_slug,
        'category':  category,
        'product':   product,
        'variants':  variants
    })

def _apply_filters(request, base_qs):
    """Застосовує GET-фільтри до базового queryset і готує список брендів із лічильниками в межах поточного QS."""
    qs = base_qs

    selected_brands = request.GET.getlist('brand')  # ?brand=whiskas&brand=royal...
    price_min       = request.GET.get('price_min') or None
    price_max       = request.GET.get('price_max') or None
    in_stock        = request.GET.get('in_stock')

    if selected_brands:
        qs = qs.filter(brand__brand_slug__in=selected_brands)

    if price_min:
        qs = qs.filter(price__gte=price_min)
    if price_max:
        qs = qs.filter(price__lte=price_max)
    if in_stock:
        # підлаштуй під свою модель складу; приклад через related_name variants.stock
        qs = qs.filter(variants__warehouse_quantity__gt=0).distinct()

    # Бренди та їх кількість САМЕ в межах відфільтрованого списку
    brands_agg = (
        qs.values('brand__brand_slug', 'brand__name')
          .annotate(count=Count('id'))
          .order_by('brand__name')
    )

    # Помітимо вибрані бренди (для чекбоксів)
    brands_ctx = [
        {
            'slug':    b['brand__brand_slug'],
            'name':  b['brand__name'],
            'count': b['count'],
            'checked': b['brand__brand_slug'] in selected_brands
        }
        for b in brands_agg if b['brand__brand_slug']  # захист від None
    ]

    return qs, {
        'brands':    brands_ctx,
        'price_min': price_min or '',
        'price_max': price_max or '',
        'in_stock':  bool(in_stock),
        'selected_brands': selected_brands
    }

def catalog_by_brand(request, brand_slug):
    brand = get_object_or_404(Brand, brand_slug__iexact=brand_slug)
    products = (Product.objects
                .filter(brand=brand)
                .select_related('brand', 'category'))
    # опційно — бренди для сайдбара
    brands = (Brand.objects
              .filter(country_slug__iexact=brand.country_slug)
              .annotate(count=Count('products')))
    return render(request, 'zoosvit/products/product_list.html', {
        'title': f'Бренд: {brand.name}',
        'products': products,
        'brands': brands,   # якщо треба фільтр збоку
    })

def catalog_by_country(request, country_slug):
    country_brands = Brand.objects.filter(country_slug__iexact=country_slug)
    products = (Product.objects
                .filter(brand__in=country_brands)
                .select_related('brand', 'category'))
    title = f"Країна: {country_brands.first().country if country_brands else country_slug}"
    return render(request, 'zoosvit/products/product_list.html', {
        'title': title,
        'products': products,
        'brands': country_brands.annotate(count=Count('products')),  # опційно
    })
