from django.contrib import admin
from .models import Order, OrderItem, PaymentTransaction


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'retail_price', 'line_total')
    readonly_fields = ('line_total',)


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    fields = ('transaction_type', 'status', 'amount', 'payment_system', 'created_at')
    readonly_fields = ('transaction_type', 'status', 'amount', 'payment_system', 'created_at')
    can_delete = False
    max_num = 0  # Не дозволяємо додавати нові


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'full_name', 'phone', 'status', 
                    'payment_method_display', 'payment_status_display', 
                    'total_amount', 'created_at', 'exported')
    list_filter = ('status', 'payment_method', 'payment_status', 'exported', 
                   'sale_type', 'delivery_condition', 'created_at')
    search_fields = ('order_number', 'full_name', 'phone', 'email', 'user__username')
    readonly_fields = ('order_number', 'total_amount', 'created_at', 'updated_at', 'exported_at')
    inlines = [OrderItemInline, PaymentTransactionInline]
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('user', 'status', 'order_number')
        }),
        ('Дані клієнта', {
            'fields': ('full_name', 'phone', 'email')
        }),
        ('Доставка', {
            'fields': ('sale_type', 'delivery_condition', 'delivery_address', 'comment')
        }),
        ('Оплата', {
            'fields': ('payment_method', 'payment_status', 'payment_id'),
            'classes': ('wide',)
        }),
        ('Експорт', {
            'fields': ('exported', 'exported_at'),
            'classes': ('collapse',)
        }),
        ('Системна інформація', {
            'fields': ('created_at', 'updated_at', 'total_amount'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_completed', 
               'mark_payment_as_paid', 'export_selected']
    
    def payment_method_display(self, obj):
        icons = {
            'cash': '💵',
            'card_online': '💳',
        }
        icon = icons.get(obj.payment_method, '❓')
        return f"{icon} {obj.get_payment_method_display()}"
    payment_method_display.short_description = 'Спосіб оплати'
    
    def payment_status_display(self, obj):
        status_colors = {
            'pending': '🟡',
            'paid': '🟢',
            'failed': '🔴',
        }
        icon = status_colors.get(obj.payment_status, '⚪')
        status_text = {
            'pending': 'Очікує',
            'paid': 'Оплачено',
            'failed': 'Не пройшла',
        }.get(obj.payment_status, obj.payment_status)
        return f"{icon} {status_text}"
    payment_status_display.short_description = 'Статус оплати'
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_PROCESSING)
        self.message_user(request, f'{updated} замовлень позначено як "Обробляється"')
    mark_as_processing.short_description = 'Позначити як "Обробляється"'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_SHIPPED)
        self.message_user(request, f'{updated} замовлень позначено як "В дорозі"')
    mark_as_shipped.short_description = 'Позначити як "В дорозі"'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status=Order.STATUS_COMPLETED)
        self.message_user(request, f'{updated} замовлень позначено як "Виконане"')
    mark_as_completed.short_description = 'Позначити як "Виконане"'
    
    def mark_payment_as_paid(self, request, queryset):
        updated = queryset.filter(payment_method='card_online').update(payment_status='paid')
        self.message_user(request, f'{updated} оплат позначено як "Оплачено"')
    mark_payment_as_paid.short_description = '💳 Позначити оплату як успішну'
    
    def export_selected(self, request, queryset):
        from django.core.management import call_command
        call_command('export_orders')
        self.message_user(request, 'Замовлення експортовано')
    export_selected.short_description = 'Експортувати в JSON'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items__product', 'items__variant')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'variant', 'quantity', 'retail_price', 'line_total')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('order__order_number', 'product__name', 'variant__sku')
    readonly_fields = ('line_total',)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link', 'transaction_type', 'status_display', 
                    'amount', 'payment_system', 'created_at', 'completed_at')
    list_filter = ('transaction_type', 'status', 'payment_system', 'created_at')
    search_fields = ('order__order_number', 'external_id', 'order__full_name')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'request_data', 'response_data')
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('order', 'transaction_type', 'status', 'amount', 'currency')
        }),
        ('Платіжна система', {
            'fields': ('payment_system', 'external_id')
        }),
        ('Деталі транзакції', {
            'fields': ('request_data', 'response_data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Часові мітки', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">#{}</a>', url, obj.order.order_number or obj.order.id)
    order_link.short_description = 'Замовлення'
    
    def status_display(self, obj):
        status_icons = {
            'initiated': '🔵',
            'processing': '🟡',
            'success': '🟢',
            'failed': '🔴',
            'cancelled': '⚫',
        }
        icon = status_icons.get(obj.status, '⚪')
        return f"{icon} {obj.get_status_display()}"
    status_display.short_description = 'Статус'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('order')
