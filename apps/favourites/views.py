from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from .models import Favourite
from apps.products.models import Product, Product_Variant
from django.views.decorators.http import require_http_methods

@require_http_methods(['POST', 'GET'])
def toggle(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)

    variant_id = request.POST.get('variant') or request.GET.get('variant')
    variant = None
    if variant_id:
        variant = get_object_or_404(Product_Variant, pk=variant_id, is_active=True)
        if variant.product_id != product.id:
            return HttpResponseBadRequest('Variant does not belong to product')

    if request.user.is_authenticated:
        fav, created = Favourite.objects.get_or_create(
            user=request.user, product=product, variant=variant
        )
        if created:
            state = 'added'
        else:
            fav.delete()
            state = 'removed'

        count = Favourite.objects.filter(user=request.user).count()
        request.session['fav_count'] = count
        return JsonResponse({
            'ok': True,
            'state': state,
            'count': count,
            'variant': variant.id if variant else None,
            'product': product.id,
        })


    fav_var_ids = set(map(int, request.session.get('fav_variant_ids', [])))
    fav_prod_ids = set(map(int, request.session.get('fav_product_ids', [])))

    if variant:
        if variant.id in fav_var_ids:
            fav_var_ids.remove(variant.id)
            state = 'removed'
        else:
            fav_var_ids.add(variant.id)
            state = 'added'
    else:
        if product.id in fav_prod_ids:
            fav_prod_ids.remove(product.id)
            state = 'removed'
        else:
            fav_prod_ids.add(product.id)
            state = 'added'

    request.session['fav_variant_ids'] = list(fav_var_ids)
    request.session['fav_product_ids'] = list(fav_prod_ids)
    total = len(fav_var_ids) + len(fav_prod_ids)

    return JsonResponse({
        'ok': True,
        'state': state,
        'count': total,
        'variant': variant.id if variant else None,
    })


def favourite_list(request):
    if request.user.is_authenticated:
        # Показуємо тільки активні товари та варіанти
        favs = (Favourite.objects
                .filter(user=request.user, product__is_active=True)
                .select_related('product', 'variant', 'product__brand', 'product__category'))
        
        # Додатково фільтруємо варіанти
        favs = [f for f in favs if not f.variant or f.variant.is_active]
        
        fav_ids = set(f.product_id for f in favs)
        fav_variant_ids = [f.variant_id for f in favs if f.variant_id]
    else:
        fav_var_ids = list(map(int, request.session.get('fav_variant_ids', [])))
        fav_prod_ids = list(map(int, request.session.get('fav_product_ids', [])))

        favs = []
        # Показуємо тільки активні товари
        products = {p.id: p for p in Product.objects.filter(id__in=fav_prod_ids, is_active=True).select_related('brand', 'category')}
        for pid in fav_prod_ids:
            p = products.get(pid)
            if p:
                favs.append(type('F', (), {'product': p, 'variant': None, 'id': f'p-{pid}'}))

        # Показуємо тільки активні варіанти
        variants = list(Product_Variant.objects.filter(id__in=fav_var_ids, is_active=True, product__is_active=True).select_related('product', 'product__brand', 'product__category'))
        for v in variants:
            favs.append(type('F', (), {'product': v.product, 'variant': v, 'id': f'v-{v.id}'}))

        fav_ids = set(fav_prod_ids) | set(v.product_id for v in variants)
        fav_variant_ids = fav_var_ids

    return render(request, 'zoosvit/favourites/favourites_list.html', {
        'title': 'Моє обране',
        'favs': favs,
        'fav_ids': fav_ids,
        'fav_product_ids': list(fav_ids),
        'fav_variant_ids': fav_variant_ids,
    })



def api_count(request):
    """Кількість улюблених для бейджика в шапці."""
    if request.user.is_authenticated:
        c = Favourite.objects.filter(user=request.user, product__is_active=True).count()
    else:
        c = len(request.session.get('fav_variant_ids', [])) + \
            len(request.session.get('fav_product_ids', []))
    return JsonResponse({'count': c})
