from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'retail_price', 'line_total')
    readonly_fields = ('line_total',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'full_name', 'phone', 'status', 
                    'total_amount', 'created_at', 'exported')
    list_filter = ('status', 'exported', 'sale_type', 'delivery_condition', 'created_at')
    search_fields = ('order_number', 'full_name', 'phone', 'email', 'user__username')
    readonly_fields = ('order_number', 'total_amount', 'created_at', 'updated_at', 'exported_at')
    inlines = [OrderItemInline]
    
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
        ('Експорт', {
            'fields': ('exported', 'exported_at'),
            'classes': ('collapse',)
        }),
        ('Системна інформація', {
            'fields': ('created_at', 'updated_at', 'total_amount'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_completed', 'export_selected']
    
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
