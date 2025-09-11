# zoosvit/context_processors.py
from apps.favourites.models import Favourite

def fav_count(request):
    # 1) пробуємо взяти з сесії (без БД)
    s_count = request.session.get('fav_count', None)
    if s_count is not None:
        return {'fav_count': s_count}

    # 2) fallback (один раз) → покласти в сесію
    if request.user.is_authenticated:
        c = Favourite.objects.filter(user=request.user).count()
    else:
        c = len(request.session.get('fav_variant_ids', [])) + \
            len(request.session.get('fav_product_ids', []))

    request.session['fav_count'] = c
    return {'fav_count': c}
