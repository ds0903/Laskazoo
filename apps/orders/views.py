# apps/orders/views.py
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from .forms import OrderCheckoutForm
from apps.products.models import Product, Product_Variant
from django.contrib import messages
from django.db.models import F, Sum, DecimalField, ExpressionWrapper

def _get_cart(user):
    return Order.objects.filter(user=user, status=Order.STATUS_CART).first()


def _cart_math(user):
    order = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
    if not order:
        return 0, 0, Decimal('0')
    qty = order.items.aggregate(q=Sum('quantity'))['q'] or 0
    line_total = ExpressionWrapper(
        F('quantity') * F('retail_price'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    total = order.items.aggregate(t=Sum(line_total))['t'] or Decimal('0')
    count = order.items.count()
    return count, qty, total

@login_required
def api_cart_summary(request):
    count, qty, total = _cart_math(request.user)
    # Decimal → str, щоб не ловити JSON serialize error
    return JsonResponse({'count': count, 'qty': qty, 'total': str(total)})

# -------- core actions --------
@login_required
def add_variant_to_cart(request, variant_id: int):
    variant = get_object_or_404(Product_Variant, pk=variant_id)

    if variant.warehouse_quantity is not None and variant.warehouse_quantity <= 0:
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': 'Немає в наявності'}, status=400)
        messages.warning(request, 'Немає в наявності.')
        return redirect('orders:cart')

    order, _ = Order.objects.get_or_create(user=request.user, status=Order.STATUS_CART)
    item, _ = OrderItem.objects.get_or_create(
        order=order, product=variant.product, variant=variant,
        defaults={'retail_price': variant.retail_price, 'quantity': 0}
    )
    new_qty = item.quantity + 1
    if variant.warehouse_quantity is not None and new_qty > variant.warehouse_quantity:
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': f'Доступно лише {variant.warehouse_quantity} шт.'}, status=400)
        messages.warning(request, f'Доступно лише {variant.warehouse_quantity} шт.')
        return redirect('orders:cart')

    item.quantity = new_qty
    item.retail_price = variant.retail_price
    item.save(update_fields=['quantity', 'retail_price'])

    if _is_ajax(request):
        lines, qty = _cart_numbers(request.user)
        count, qty, total = _cart_math(request.user)
        return JsonResponse({'ok': True, 'count': count, 'qty': qty, 'total': str(total)}, status=201)
    messages.success(request, f'Додано: {variant.product.name}')
    return redirect('orders:cart')

@login_required
def add_to_cart(request, product_id: int):
    variant_id = request.GET.get('variant')
    if variant_id:
        return add_variant_to_cart(request, variant_id)

    product = get_object_or_404(Product, pk=product_id)

    # якщо є варіанти — делегуємо
    v = (Product_Variant.objects
         .filter(product=product)
         .order_by('retail_price')
         .filter(stock__gt=0).first()
         or Product_Variant.objects.filter(product=product).order_by('retail_price').first())
    if v:
        return add_variant_to_cart(request, v.id)

    order, _ = Order.objects.get_or_create(user=request.user, status=Order.STATUS_CART)
    item, _ = OrderItem.objects.get_or_create(
        order=order, product=product, variant=None,
        defaults={'retail_price': product.retail_price, 'quantity': 0}
    )
    item.quantity += 1
    if product.retail_price is not None:
        item.retail_price = product.retail_price
    item.save(update_fields=['quantity', 'retail_price'])

    if _is_ajax(request):
        order, _ = _cart_tuple(request.user)
        lines, qty = _cart_numbers(request.user)
        count, qty, total = _cart_math(request.user)
        return JsonResponse({'ok': True, 'count': count, 'qty': qty, 'total': str(total)}, status=201)
    messages.success(request, f'Додано: {product.name}')
    return redirect('orders:cart')

@login_required
@require_POST
def item_set_qty(request, item_id):
    order = Order.objects.filter(user=request.user, status=Order.STATUS_CART).first()
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    try:
        qty = int(request.POST.get('qty', '1'))
    except ValueError:
        qty = 1
    if qty < 1:
        qty = 1
    if item.variant and item.variant.warehouse_quantity is not None:
        qty = min(qty, int(item.variant.warehouse_quantity))

    item.quantity = qty
    item.save(update_fields=['quantity'])

    # ⚠️ Не передаємо _cart_math у render — повертаємо готовий фрагмент
    return cart_modal(request)

@login_required
def cart_detail(request):
    order = Order.objects.filter(user=request.user, status=Order.STATUS_CART).first()
    total = Decimal('0')
    if order:
        line_total = ExpressionWrapper(F('quantity') * F('retail_price'),
                                       output_field=DecimalField(max_digits=12, decimal_places=2))
        total = order.items.aggregate(total=Sum(line_total))['total'] or 0
    return render(request, 'zoosvit/orders/cart.html', {'order': order, 'total': total})

@login_required
def checkout(request):
    order = get_object_or_404(Order, user=request.user, status=Order.STATUS_CART)
    if request.method == 'POST':
        form = OrderCheckoutForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = Order.STATUS_NEW
            order.save()
            return redirect('orders:history')
    else:
        form = OrderCheckoutForm(instance=order)
    return render(request, 'zoosvit/orders/checkout.html', {'order': order, 'form': form})

@login_required
def orders_list(request):
    qs = Order.objects.filter(user=request.user).exclude(status=Order.STATUS_CART)
    return render(request, 'orders/history.html', {'orders': qs})

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

# --- Нові дії з айтемами кошика ---
@login_required
def cart_item_inc(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status=Order.STATUS_CART)
    item.quantity += 1
    item.save(update_fields=['quantity'])
    return redirect('orders:cart')

@login_required
def cart_item_dec(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status=Order.STATUS_CART)
    if item.quantity > 1:
        item.quantity -= 1
        item.save(update_fields=['quantity'])
    else:
        item.delete()
    return redirect('orders:cart')

@login_required
def cart_item_remove(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status=Order.STATUS_CART)
    item.delete()
    messages.info(request, 'Позицію видалено з кошика.')
    return redirect('orders:cart')

@login_required
def cart_clear(request):
    order = _get_cart(request.user)
    if order:
        order.items.all().delete()
        messages.info(request, 'Кошик очищено.')
    return redirect('orders:cart')


# -------- helpers --------
def _is_ajax(request):
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.headers.get('HX-Request') == 'true'
        or request.GET.get('ajax') == '1'
    )

def _cart_tuple(user):
    order = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
    total = Decimal('0')
    if order:
        line_total = ExpressionWrapper(
            F('quantity') * F('retail_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
        total = order.items.aggregate(total=Sum(line_total))['total'] or Decimal('0')
    return order, total

# ----- модалка -----
@login_required
def cart_modal(request):
    order, total = _cart_tuple(request.user)
    return render(request, 'zoosvit/orders/_cart_modal_body.html', {'order': order, 'total': total})

def _cart_numbers(user):
    """Повертає (lines_count, total_qty) для кошика користувача."""
    order = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
    if not order:
        return 0, 0
    lines = order.items.count()
    qty = order.items.aggregate(q=Sum('quantity'))['q'] or 0
    return lines, qty

# ----- повна сторінка (залишаємо як fallback) -----
@login_required
def cart_detail(request):
    order, total = _cart_tuple(request.user)
    return render(request, 'zoosvit/orders/cart.html', {'order': order, 'total': total})

# ----- інк/дек/видалення: якщо AJAX — повертаємо одразу HTML модалки -----
@login_required
def cart_item_inc(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status=Order.STATUS_CART)
    # перевірка складу для варіанта
    if item.variant and item.variant.warehouse_quantity is not None and item.quantity + 1 > item.variant.warehouse_quantity:
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': 'Перевищено доступний склад'}, status=400)
        messages.warning(request, 'Перевищено доступний склад')
    else:
        item.quantity += 1
        item.save(update_fields=['quantity'])
    if _is_ajax(request):
        return cart_modal(request)
    return redirect('orders:cart')

@login_required
def cart_item_dec(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status=Order.STATUS_CART)
    if item.quantity > 1:
        item.quantity -= 1
        item.save(update_fields=['quantity'])
    else:
        item.delete()
    if _is_ajax(request):
        return cart_modal(request)
    return redirect('orders:cart')

@login_required
def cart_item_remove(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status=Order.STATUS_CART)
    item.delete()
    if _is_ajax(request):
        return cart_modal(request)
    return redirect('orders:cart')

@login_required
def cart_clear(request):
    order = Order.objects.filter(user=request.user, status=Order.STATUS_CART).first()
    if order:
        order.items.all().delete()
    if _is_ajax(request):
        return cart_modal(request)
    return redirect('orders:cart')