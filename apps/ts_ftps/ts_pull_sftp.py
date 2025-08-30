from django.core.management.base import BaseCommand
from services import import_from_source

class Command(BaseCommand):
    help = "Імпорт товарів з TSGoods.trs (SFTP або локальна папка)"

    def handle(self, *args, **opts):
        res = import_from_source()
        self.stdout.write(self.style.SUCCESS(f"Імпорт завершено: upserted={res['upserted']} total={res['total']}"))
