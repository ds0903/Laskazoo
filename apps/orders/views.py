# apps/orders/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Order

@login_required
def order_list(request):
    """
    Список всіх замовлень поточного користувача
    """
    orders = request.user.orders.all()  # через related_name
    return render(request, 'zoosvit/orders/order_list.html', {
        'orders': orders
    })

@login_required
def order_detail(request, pk):
    """
    Деталі одного замовлення, перевіримо, що належить поточному юзеру
    """
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'zoosvit/orders/order_detail.html', {
        'order': order
    })
