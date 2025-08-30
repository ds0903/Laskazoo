from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from .models import Order
from decimal import Decimal

def cart_summary(request):
    qty = 0
    total = Decimal('0')
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, status=Order.STATUS_CART).first()
        if order:
            qty = order.items.aggregate(q=Sum('quantity'))['q'] or 0
            line_total = ExpressionWrapper(F('quantity') * F('retail_price'),
                                           output_field=DecimalField(max_digits=12, decimal_places=2))
            total = order.items.aggregate(t=Sum(line_total))['t'] or Decimal('0')
    return {'cart_qty': qty, 'cart_total': total}