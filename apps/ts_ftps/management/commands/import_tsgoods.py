# apps/products/management/commands/import_tsgoods.py
from django.core.management.base import BaseCommand
from apps.ts_ftps.services import import_ts_goods

class Command(BaseCommand):
    help = "Імпорт TSGoods.trs у сиру таблицю ts_goods через FTPS/FTP/LOCAL"

    def add_arguments(self, parser):
        g = parser.add_mutually_exclusive_group()
        g.add_argument('--replace', action='store_true',
                       help='Повністю замінити вміст таблиці (truncate + load)')
        g.add_argument('--append', action='store_true',
                       help='Лише створювати нові, існуючі НЕ оновлювати')
        # за замовчуванням буде upsert

    def handle(self, *args, **options):
        mode = 'replace' if options['replace'] else ('append' if options['append'] else 'upsert')
        res = import_ts_goods(mode=mode)
        self.stdout.write(self.style.SUCCESS(
            f"OK mode={mode}: total={res['total']} "
            f"created={res.get('created',0)} updated={res.get('updated',0)} skipped={res.get('skipped',0)}"
        ))
