from .models import Favourite

def fav_counter(request):
    try:
        if request.user.is_authenticated:
            return {'fav_count': Favourite.objects.filter(user=request.user).count()}
        ids = request.session.get('fav_ids', [])
        return {'fav_count': len(ids)}
    except Exception:
        return {'fav_count': 0}
