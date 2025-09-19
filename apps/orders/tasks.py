from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task
def export_orders_task():
    """
    Періодичний експорт замовлень в JSON для TorgSoft
    Запускається кожні 15 хвилин через Celery Beat
    """
    try:
        call_command('export_orders')
        logger.info('Orders exported successfully')
        return 'Orders exported successfully'
    except Exception as e:
        logger.error(f'Error exporting orders: {str(e)}')
        raise
