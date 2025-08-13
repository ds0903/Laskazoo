from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import Favourite

@receiver(user_logged_in)
def merge_session_favs(sender, user, request, **kwargs):
    ids = request.session.get('fav_ids', [])
    for pid in ids:
        Favourite.objects.get_or_create(user=user, product_id=pid)
    if ids:
        request.session['fav_ids'] = []
        request.session.modified = True
