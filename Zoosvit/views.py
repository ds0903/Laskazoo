# Zoosvit/views.py (або де у тебе home)
from django.shortcuts import render
from apps.products.models import PopularProduct, Product_Variant
from apps.favourites.models import Favourite

def home(request):
    populars = (PopularProduct.objects
                .select_related('product', 'product__brand', 'product__category')
                .order_by('position')
                .filter(is_active=True)[:20])

    product_ids = [pp.product_id for pp in populars]
    variants = (Product_Variant.objects
                .filter(product_id__in=product_ids)
                .order_by('price'))  # або як хочеш сортувати

    by_pid = {}
    for v in variants:
        by_pid.setdefault(v.product_id, []).append(v)

    # прикріпимо заздалегідь зібрані варіанти до об’єктів продуктів
    for pp in populars:
        pp.product.variants_for_card = by_pid.get(pp.product_id, [])

    # обрані товари
    if request.user.is_authenticated:
        fav_ids = set(
            Favourite.objects
            .filter(user=request.user, product_id__in=product_ids)
            .values_list('product_id', flat=True)
        )
    else:
        fav_ids = set(request.session.get('fav_ids', []))

    return render(request, 'zoosvit/home.html', {
        'populars': populars,
        'fav_ids': fav_ids,
    })
