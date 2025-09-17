from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Створює тестові замовлення для перевірки експорту'

    def handle(self, *args, **options):
        # Створюємо тестового користувача, якщо його немає
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Тест',
                'last_name': 'Користувач'
            }
        )
        
        # Беремо перший продукт для тесту
        product = Product.objects.first()
        if not product:
            self.stdout.write(self.style.ERROR('Немає продуктів для створення тестового замовлення'))
            return
        
        # Створюємо тестове замовлення
        order = Order.objects.create(
            user=user,
            status=Order.STATUS_IN_PROCESS,  # Статус "в обробці"
            full_name="Тестовий Покупець Петрович",
            phone="+380671234567",
            email="test@buyer.com",
            delivery_condition="nova_poshta",
            delivery_address="Київ, вул. Тестова 123, Відділення №1",
            comment="Тестове замовлення для перевірки експорту",
            sale_type="1"
        )
        
        # Додаємо товар до замовлення
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2,
            retail_price=Decimal('199.50')
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Створено тестове замовлення #{order.id} для користувача {user.username}\\n'
                f'Статус: {order.get_status_display()}\\n'
                f'Товар: {product.name} x 2 шт'
            )
        )
