from decimal import Decimal
from typing import List, Dict

from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum, DecimalField, ExpressionWrapper

from .models import Order, OrderItem
from .forms import OrderCheckoutForm
from apps.products.models import Product, Product_Variant

from .session_cart import summary as sess_summary, add_item as sess_add, CART_KEY


def _is_ajax(request):
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.headers.get('HX-Request') == 'true'
        or request.GET.get('ajax') == '1'
    )

def _get_cart(user):
    return Order.objects.filter(user=user, status=Order.STATUS_CART).first()

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

def _cart_numbers(user):
    order = Order.objects.filter(user=user, status=Order.STATUS_CART).first()
    if not order:
        return 0, 0
    lines = order.items.count()
    qty = order.items.aggregate(q=Sum('quantity'))['q'] or 0
    return lines, qty


def api_cart_summary(request):
    if request.user.is_authenticated:
        count, qty, total = _cart_math(request.user)
    else:
        count, qty, total = sess_summary(request.session)
    return JsonResponse({'count': count, 'qty': qty, 'total': str(total)})

def cart_modal(request):
    """
    Тіло модалки кошика. НЕ login_required — гостям показуємо call-to-action.
    Рендеримо один і той же шаблон _cart_modal_body.html, де є гілки:
      - {# 1) Авторизований #} через змінні order, total
      - {# 2) Гість #} через змінні sitems, total
    """
    if request.user.is_authenticated:
        order, total = _cart_tuple(request.user)
        return render(request, 'zoosvit/orders/_cart_modal_body.html', {'order': order, 'total': total})

    items: List[Dict] = request.session.get(CART_KEY, []) or []
    sitems: List[Dict] = []
    total = Decimal('0')

    for idx, it in enumerate(items):
        kind = it.get('kind')
        obj_id = int(it.get('id'))
        qty = int(it.get('qty', 1))
        price = Decimal(str(it.get('price', '0')))
        line = qty * price

        name = sku = weight = size = ''
        thumb_url = None

        if kind == 'variant':
            v = Product_Variant.objects.select_related('product').filter(pk=obj_id).first()
            if v:
                name = v.product.name
                sku = v.sku or ''
                weight = v.weight or ''
                size = v.size or ''
                thumb_url = (getattr(v, 'image', None) and v.image.url) \
                            or (getattr(v.product, 'image', None) and v.product.image.url)
        else:
            p = Product.objects.filter(pk=obj_id).first()
            if p:
                name = p.name
                thumb_url = getattr(p, 'image', None) and p.image.url

        total += line
        sitems.append({
            'sid': idx,
            'name': name,
            'sku': sku,
            'weight': weight,
            'size': size,
            'qty': qty,
            'line': line,
            'thumb': thumb_url,
        })

    return render(request, 'zoosvit/orders/_cart_modal_body.html', {'sitems': sitems, 'total': total})


def add_variant_to_cart(request, variant_id: int):
    variant = get_object_or_404(Product_Variant, pk=variant_id)

    if variant.warehouse_quantity is not None and variant.warehouse_quantity <= 0:
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': 'Немає в наявності'}, status=400)
        messages.warning(request, 'Немає в наявності.')
        return redirect('orders:cart')

    if request.user.is_authenticated:
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
            count, qty, total = _cart_math(request.user)
            return JsonResponse({'ok': True, 'count': count, 'qty': qty, 'total': str(total)}, status=201)
        messages.success(request, f'Додано: {variant.product.name}')
        return redirect('orders:cart')

    sess_add(request.session, 'variant', variant.id, price=variant.retail_price, inc=1)
    if _is_ajax(request):
        lines, qty, total = sess_summary(request.session)
        return JsonResponse({'ok': True, 'count': lines, 'qty': qty, 'total': str(total)}, status=201)
    return redirect('orders:cart')

def add_to_cart(request, product_id: int):
    variant_id = request.GET.get('variant')
    if variant_id:
        return add_variant_to_cart(request, variant_id)

    product = get_object_or_404(Product, pk=product_id)

    v = (Product_Variant.objects
         .filter(product=product)
         .order_by('retail_price')
         .filter(warehouse_quantity__gt=0).first()
         or Product_Variant.objects.filter(product=product).order_by('retail_price').first())
    if v:
        return add_variant_to_cart(request, v.id)

    if request.user.is_authenticated:
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
            count, qty, total = _cart_math(request.user)
            return JsonResponse({'ok': True, 'count': count, 'qty': qty, 'total': str(total)}, status=201)
        messages.success(request, f'Додано: {product.name}')
        return redirect('orders:cart')

    price = product.retail_price or Decimal('0')
    sess_add(request.session, 'product', product.id, price=price, inc=1)
    if _is_ajax(request):
        lines, qty, total = sess_summary(request.session)
        return JsonResponse({'ok': True, 'count': lines, 'qty': qty, 'total': str(total)}, status=201)
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
    return cart_modal(request)

@login_required
def cart_detail(request):
    order, total = _cart_tuple(request.user)
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
    orders = request.user.orders.all()
    return render(request, 'zoosvit/orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'zoosvit/orders/order_detail.html', {'order': order})


def _sess_get_items(request):
    return list(request.session.get(CART_KEY, []) or [])

def _sess_save_items(request, items):
    request.session[CART_KEY] = items
    request.session.modified = True

def cart_item_inc(request, item_id: int):
    if request.user.is_authenticated and not request.GET.get('guest'):
        item = get_object_or_404(
            OrderItem, id=item_id,
            order__user=request.user, order__status=Order.STATUS_CART
        )
        if item.variant and item.variant.warehouse_quantity is not None \
           and item.quantity + 1 > item.variant.warehouse_quantity:
            return JsonResponse({'ok': False, 'message': 'Перевищено доступний склад'}, status=400) if _is_ajax(request) \
                   else redirect('orders:cart')
        item.quantity += 1
        item.save(update_fields=['quantity'])
    else:
        sid = int(item_id)
        items = _sess_get_items(request)
        if 0 <= sid < len(items):
            items[sid]['qty'] = int(items[sid].get('qty', 1)) + 1
            _sess_save_items(request, items)
    return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')

def cart_item_dec(request, item_id: int):
    if request.user.is_authenticated and not request.GET.get('guest'):
        item = get_object_or_404(
            OrderItem, id=item_id,
            order__user=request.user, order__status=Order.STATUS_CART
        )
        if item.quantity > 1:
            item.quantity -= 1
            item.save(update_fields=['quantity'])
        else:
            item.delete()
    else:
        sid = int(item_id)
        items = _sess_get_items(request)
        if 0 <= sid < len(items):
            q = int(items[sid].get('qty', 1)) - 1
            if q <= 0:
                items.pop(sid)
            else:
                items[sid]['qty'] = q
            _sess_save_items(request, items)
    return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')

def cart_item_remove(request, item_id: int):
    if request.user.is_authenticated and not request.GET.get('guest'):
        item = get_object_or_404(
            OrderItem, id=item_id,
            order__user=request.user, order__status=Order.STATUS_CART
        )
        item.delete()
    else:
        sid = int(item_id)
        items = _sess_get_items(request)
        if 0 <= sid < len(items):
            items.pop(sid)
            _sess_save_items(request, items)
    return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')

def cart_clear(request):
    if request.user.is_authenticated and not request.GET.get('guest'):
        order = Order.objects.filter(user=request.user, status=Order.STATUS_CART).first()
        if order:
            order.items.all().delete()
    else:
        _sess_save_items(request, [])
    return cart_modal(request) if _is_ajax(request) else redirect('orders:cart')

