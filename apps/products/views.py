from django.shortcuts import render, get_object_or_404
from .models import Main_Categories, Category, Product, Brand, Product_Variant
from django.db.models import Count, Q, Prefetch
from django.shortcuts import redirect
from django.http import JsonResponse
from decimal import Decimal
from django.db.models import (
    Q, F, Count, Min, Value, IntegerField,
)
from django.urls import reverse
from django.db.models.functions import Coalesce
from django.db.models import Q, Case, When, Value, IntegerField, Min
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


try:
    from apps.favourites.models import Favourite
except Exception:
    Favourite = None

def search_suggest(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"items": []})


    qs = (
        Product.objects.filter(Q(name__icontains=q))
        .annotate(
            score=Case(
                When(name__iexact=q, then=Value(100)),
                When(name__istartswith=q, then=Value(85)),
                default=Value(60),
                output_field=IntegerField(),
            ),

            price=Coalesce(Min("variants__retail_price"), "retail_price"),
        )
        .order_by("-score")[:3]
    )

    items = []
    for p in qs:
        items.append({
            "id": p.id,
            "name": p.name,
            "url": p.get_absolute_url() if hasattr(p, "get_absolute_url") else reverse("products:detail", args=[p.id]),
            "image": (p.image.url if getattr(p, "image", None) else ""),
            "price": float(p.price) if p.price is not None else None,
        })
    return JsonResponse({"items": items})

def quick_search(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return redirect(reverse("products:catalog"))


    pqs = Product.objects.filter(name__icontains=q, is_active=True).annotate(
        score=Case(
            When(name__iexact=q, then=Value(100)),
            When(name__istartswith=q, then=Value(80)),
            default=Value(50),
            output_field=IntegerField(),
        )
    ).values("id", "score")


    vqs = Product_Variant.objects.filter(name__icontains=q).select_related("product").annotate(
        score=Case(
            When(name__iexact=q, then=Value(100)),
            When(name__istartswith=q, then=Value(75)),
            default=Value(45),
            output_field=IntegerField(),
        )
    ).values("product_id", "score")


    best_product_id = None
    best_score = -1

    for row in pqs:
        if row["score"] > best_score:
            best_score = row["score"]
            best_product_id = row["id"]

    for row in vqs:
        if row["score"] > best_score:
            best_score = row["score"]
            best_product_id = row["product_id"]

    if best_product_id:
        try:
            prod = Product.objects.get(id=best_product_id)
            return redirect(prod.get_absolute_url())
        except Product.DoesNotExist:
            pass


    return redirect(f'{reverse("products:catalog")}?q={q}')

def catalog(request):
    mains = Main_Categories.objects.filter(is_active=True).order_by('id')

    variants_qs = (
        Product_Variant.objects
        .only('id', 'product_id', 'sku', 'retail_price', 'weight', 'size', 'image', 'warehouse_quantity', 'is_active')
        .order_by('retail_price')
    )

    base_qs = (
        Product.objects
        .select_related('brand', 'category')
        .prefetch_related(
            Prefetch('variants', queryset=variants_qs, to_attr='variants_for_card')
        )
    )

    products_qs, filt_ctx = _apply_filters(request, base_qs)
    
    # Додаємо пагінацію
    items_per_page = int(request.GET.get('per_page', 20))  # 20 товарів на сторінку за замовчуванням
    if items_per_page > 100:  # обмежуємо максимум
        items_per_page = 100
    
    paginator = Paginator(products_qs, items_per_page)
    page = request.GET.get('page', 1)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    if request.user.is_authenticated:
        fav_qs = Favourite.objects.filter(user=request.user)
        fav_variant_ids = list(
            fav_qs.exclude(variant__isnull=True).values_list('variant_id', flat=True)
        )
        fav_product_ids = list(
            fav_qs.filter(variant__isnull=True).values_list('product_id', flat=True)
        )
    else:
        fav_variant_ids = list(map(int, request.session.get('fav_variant_ids', [])))
        fav_product_ids = list(map(int, request.session.get('fav_product_ids', [])))

    ctx = {
        'title':    'Каталог',
        'mains':    mains,
        'products': products,  # тепер це Page об'єкт
        'fav_variant_ids':  list(fav_variant_ids),
        'fav_product_ids': fav_product_ids,
        'current_per_page': items_per_page,
        **filt_ctx,
    }
    return render(request, 'zoosvit/products/catalog.html', ctx)

def subcategory_list(request, main_slug):
    main = get_object_or_404(Main_Categories, slug=main_slug, is_active=True)
    subs = main.categories.filter(is_active=True).order_by('id')
    return render(request, 'zoosvit/products/subcategory_list.html', {
        'main':       main,
        'categories': subs,
    })

def category_list(request, main_slug, slug):
    category = get_object_or_404(
        Category,
        slug=slug,
        main_category__slug=main_slug,
        is_active=True
    )


    base_qs = (
        Product.objects
        .filter(category=category)
        .select_related('brand', 'category')
        .prefetch_related('variants')
    )


    products_qs, filt_ctx = _apply_filters(request, base_qs)
    
    # Додаємо пагінацію
    items_per_page = int(request.GET.get('per_page', 20))
    if items_per_page > 100:
        items_per_page = 100
    
    paginator = Paginator(products_qs, items_per_page)
    page = request.GET.get('page', 1)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    if request.user.is_authenticated:
        fav_qs = Favourite.objects.filter(user=request.user)
        fav_variant_ids = list(
            fav_qs.exclude(variant__isnull=True).values_list('variant_id', flat=True)
        )
        fav_product_ids = list(
            fav_qs.filter(variant__isnull=True).values_list('product_id', flat=True)
        )
    else:
        fav_variant_ids = list(map(int, request.session.get('fav_variant_ids', [])))
        fav_product_ids = list(map(int, request.session.get('fav_product_ids', [])))

    return render(request, 'zoosvit/products/category_list.html', {
        'main':     category.main_category,
        'category': category,
        'products': products,
        'fav_variant_ids': list(fav_variant_ids),
        'fav_product_ids': fav_product_ids,
        'current_per_page': items_per_page,
        **filt_ctx,
    })

def product_detail(request, main_slug, slug, product_slug):

    category = get_object_or_404(
        Category,
        slug=slug,
        main_category__slug=main_slug,
        is_active=True
    )

    product = get_object_or_404(
        Product,
        slug=product_slug,
        category=category
    )

    variants = product.variants.all()

    # Додаємо логіку для обраних товарів
    if request.user.is_authenticated:
        fav_qs = Favourite.objects.filter(user=request.user)
        fav_variant_ids = list(
            fav_qs.exclude(variant__isnull=True).values_list('variant_id', flat=True)
        )
        fav_product_ids = list(
            fav_qs.filter(variant__isnull=True).values_list('product_id', flat=True)
        )
    else:
        fav_variant_ids = list(map(int, request.session.get('fav_variant_ids', [])))
        fav_product_ids = list(map(int, request.session.get('fav_product_ids', [])))

    return render(request, 'zoosvit/products/product_detail.html', {
        'main_slug': main_slug,
        'category':  category,
        'product':   product,
        'variants':  variants,
        'fav_variant_ids': fav_variant_ids,
        'fav_product_ids': fav_product_ids,
    })

def _apply_filters(request, base_qs):

    qs = base_qs

    selected_brands = request.GET.getlist('brand')
    price_min       = request.GET.get('price_min') or None
    price_max       = request.GET.get('price_max') or None
    in_stock        = request.GET.get('in_stock')
    # TODO: фільтри в бренд перенсти
    if selected_brands:
        qs = qs.filter(brand__brand_slug__in=selected_brands)

    if price_min:
        qs = qs.filter(retail_price__gte=price_min)
    if price_max:
        qs = qs.filter(retail_price__lte=price_max)
    if in_stock:
        qs = qs.filter(
            Q(is_active=True, warehouse_quantity__gt=0) |
            Q(variants__is_active=True, variants__warehouse_quantity__gt=0)
        ).distinct()
    
    # Сортування: активні товари зверху, неактивні внизу
    qs = qs.annotate(
        is_available=Case(
            When(Q(is_active=True, warehouse_quantity__gt=0), then=Value(1)),
            When(Q(variants__is_active=True, variants__warehouse_quantity__gt=0), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('-is_available', 'id').distinct()


    brands_agg = (
        base_qs.values('brand__brand_slug', 'brand__name')
          .annotate(count=Count('id'))
          .order_by('brand__name')
    )


    brands_ctx = [
        {
            'slug':    b['brand__brand_slug'],
            'name':  b['brand__name'],
            'count': b['count'],
            'checked': b['brand__brand_slug'] in selected_brands
        }
        for b in brands_agg if b['brand__brand_slug']
    ]

    return qs, {
        'brands':    brands_ctx,
        'price_min': price_min or '',
        'price_max': price_max or '',
        'in_stock':  bool(in_stock),
        'selected_brands': selected_brands
    }

def catalog_by_brand(request, brand_slug):

    cur_brand = get_object_or_404(Brand, brand_slug__iexact=brand_slug, is_active=True)


    picked_brands = request.GET.getlist('brand')           # може бути кілька
    price_min     = (request.GET.get('price_min') or '').strip()
    price_max     = (request.GET.get('price_max') or '').strip()
    in_stock      = request.GET.get('in_stock') == '1'



    base = Product.objects.all()
    if picked_brands:
        base = base.filter(brand__brand_slug__in=picked_brands)
    else:
        base = base.filter(brand=cur_brand)


    products_qs = (base
        .select_related('brand', 'category')
        .annotate(min_var_price=Min('variants__retail_price'))
        .annotate(price_eff=Coalesce('min_var_price', F('retail_price')))
    )


    if price_min:
        try: products_qs = products_qs.filter(price_eff__gte=Decimal(price_min))
        except Exception: pass
    if price_max:
        try: products_qs = products_qs.filter(price_eff__lte=Decimal(price_max))
        except Exception: pass


    if in_stock:
        products_qs = products_qs.filter(
            Q(is_active=True, warehouse_quantity__gt=0) |
            Q(variants__is_active=True, variants__warehouse_quantity__gt=0)
        )

    # Сортування: активні товари зверху, неактивні внизу
    products_qs = products_qs.annotate(
        is_available=Case(
            When(Q(is_active=True, warehouse_quantity__gt=0), then=Value(1)),
            When(Q(variants__is_active=True, variants__warehouse_quantity__gt=0), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('-is_available', 'id').distinct()
    
    # Додаємо пагінацію
    items_per_page = int(request.GET.get('per_page', 20))
    if items_per_page > 100:
        items_per_page = 100
    
    paginator = Paginator(products_qs, items_per_page)
    page = request.GET.get('page', 1)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)




    sidebar = (Product.objects.all()
        .annotate(min_var_price=Min('variants__retail_price'))
        .annotate(price_eff=Coalesce('min_var_price', F('retail_price')))
    )
    if price_min:
        try: sidebar = sidebar.filter(price_eff__gte=Decimal(price_min))
        except Exception: pass
    if price_max:
        try: sidebar = sidebar.filter(price_eff__lte=Decimal(price_max))
        except Exception: pass
    if in_stock:
        sidebar = sidebar.filter(
            Q(is_active=True, warehouse_quantity__gt=0) |
            Q(variants__is_active=True, variants__warehouse_quantity__gt=0)
        )


    sidebar = sidebar.filter(brand__country_slug__iexact=cur_brand.country_slug)

    agg = (sidebar.values('brand__brand_slug', 'brand__name')
                 .annotate(count=Count('id'))
                 .order_by('brand__name'))

    picked_set = set(picked_brands) if picked_brands else {cur_brand.brand_slug}
    brands_ctx = [
        {
            'slug':  row['brand__brand_slug'],
            'name':  row['brand__name'],
            'count': row['count'],
            'checked': row['brand__brand_slug'] in picked_set
        }
        for row in agg if row['brand__brand_slug']
    ]

    return render(request, 'zoosvit/products/product_list.html', {
        'title':     f'Бренд: {cur_brand.name}',
        'products':  products,
        'brands':    brands_ctx,
        'price_min': price_min,
        'price_max': price_max,
        'in_stock':  in_stock,
        'current_per_page': items_per_page,
    })

def catalog_by_country(request, country_slug):
    country_brands = Brand.objects.filter(country_slug__iexact=country_slug, is_active=True)
    products_qs = (Product.objects
                .filter(brand__in=country_brands)
                .select_related('brand', 'category')
                .annotate(
                    is_available=Case(
                        When(Q(is_active=True, warehouse_quantity__gt=0), then=Value(1)),
                        When(Q(variants__is_active=True, variants__warehouse_quantity__gt=0), then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ).order_by('-is_available', 'id'))
    
    # Додаємо пагінацію
    items_per_page = int(request.GET.get('per_page', 20))
    if items_per_page > 100:
        items_per_page = 100
    
    paginator = Paginator(products_qs, items_per_page)
    page = request.GET.get('page', 1)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
        
    title = f"Країна: {country_brands.first().country if country_brands else country_slug}"
    return render(request, 'zoosvit/products/product_list.html', {
        'title': title,
        'products': products,
        'brands': country_brands.annotate(count=Count('products')),
        'current_per_page': items_per_page,
    })
