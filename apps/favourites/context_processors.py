from apps.favourites.models import Favourite

def fav_count(request):
    s_count = request.session.get('fav_count', None)
    if s_count is not None:
        return {'fav_count': s_count}

    if request.user.is_authenticated:
        c = Favourite.objects.filter(user=request.user).count()
    else:
        c = len(request.session.get('fav_variant_ids', [])) + \
            len(request.session.get('fav_product_ids', []))

    request.session['fav_count'] = c
    return {'fav_count': c}
