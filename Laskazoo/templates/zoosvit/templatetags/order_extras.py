# apps/orders/templatetags/order_extras.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def mul(a, b):
    try:
        return Decimal(a) * Decimal(b)
    except Exception:
        return ''
