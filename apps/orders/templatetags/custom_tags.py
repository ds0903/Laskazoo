from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def calculate_total(order):
    """Обчислює загальну суму замовлення"""
    if hasattr(order, 'total_amount'):
        return order.total_amount
    
    total = Decimal('0')
    for item in order.items.all():
        if hasattr(item, 'line_total'):
            total += item.line_total
        else:
            total += item.retail_price * item.quantity
    return total
