# ts_ftps/management/commands/sync_ts_direct.py
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.products.models import Product, Product_Variant
from apps.ts_ftps.utils import get_reader
from apps.ts_ftps.parser import parse_rows


def money(x, default='0.00') -> Decimal:
    """
    Безпечно конвертує значення в Decimal(2):
    - приймає 19, 19.5, '19,50', ' 1 234,56 ', None
    - повертає Decimal із двома знаками після коми
    """
    if x is None:
        s = ''
    else:
        s = str(x).strip().replace('\xa0', '').replace(' ', '')
    if not s:
        s = default
    # якщо є кома і немає крапки — це десятковий роздільник
    if s.count(',') == 1 and s.count('.') == 0:
        s = s.replace(',', '.')
    # прибрати тисячні роздільники (на всяк, якщо "1,234.56")
    if s.count(',') > 0 and s.count('.') > 0:
        s = s.replace(',', '')
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError):
        d = Decimal(default)
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def as_int(x) -> int:
    try:
        return int(money(x))
    except Exception:
        try:
            return int(x or 0)
        except Exception:
            return 0


def set_if_has(obj, field, value, changes):
    if not hasattr(obj, field):
        return
    old = getattr(obj, field)
    if old != value:
        setattr(obj, field, value)
        changes.append((field, old, value))


class Command(BaseCommand):
    help = (
        "Синхронізація Product та Product_Variant з файлу Торгсофт (LOCAL/FTP/FTPS/SFTP).\n"
        "Матч ТІЛЬКИ по torgsoft_id == good_id. Якщо не знайдено — пропускаємо.\n"
        "Після матчу оновлюємо: sku←articul (якщо непорожній), barcode←barcode (якщо непорожній),\n"
        "та грошові поля: prime_cost, retail_price, wholesale_price, retail_price_with_discount (Decimal, 2 знаки),\n"
        "і warehouse_quantity (Integer)."
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry', action='store_true', help='Лише показати зміни, без збереження')
        parser.add_argument('--only-variants', action='store_true', help='Оновлювати лише Product_Variant')
        parser.add_argument('--only-products', action='store_true', help='Оновлювати лише Product')

    def handle(self, *args, **opts):
        dry = opts['dry']
        only_variants = opts['only_variants']
        only_products = opts['only_products']

        if only_variants and only_products:
            self.stdout.write(self.style.ERROR("Вибери одне: --only-variants або --only-products"))
            return

        # 1) читаємо файл
        mode, client, incoming_dir, _photos_dir, file_name = get_reader()
        trs_path = f"{incoming_dir.rstrip('/')}/{file_name}"
        if mode in ("ftp", "ftps", "sftp"):
            raw = client.read_bytes(trs_path)
        else:
            with open(trs_path, "rb") as f:
                raw = f.read()

        # 2) індексимо тільки по good_id
        ts_by_good_id = {}
        rows = list(parse_rows(raw))
        for r in rows:
            gid = (r.get('good_id') or '').strip()
            if gid:
                ts_by_good_id[gid] = r

        self.stdout.write(f"TS rows: {len(rows)} (good_id indexed: {len(ts_by_good_id)})")

        updated_cnt = 0
        preview = []

        def sync_obj(obj, label: str):
            nonlocal updated_cnt
            tid = str(getattr(obj, 'torgsoft_id', '') or '').strip()
            if not tid:
                return
            ts = ts_by_good_id.get(tid)
            if not ts:
                return

            changes = []
            need_slug = False

            old_slug = getattr(obj, 'slug', None)

            def set_if_has_track(field, value):
                nonlocal need_slug
                if not hasattr(obj, field):
                    return
                old = getattr(obj, field)
                if old != value:
                    setattr(obj, field, value)
                    changes.append((field, old, value))
                    # якщо чіпали будь-що з цих полів — перебудувати slug:
                    if field in ('name', 'sku', 'barcode'):
                        need_slug = True

            # 1) identifiers: оновлюємо ТІЛЬКИ непорожні значення з TS
            ts_barcode = (ts.get('barcode') or '').strip()
            ts_sku     = (ts.get('articul') or '').strip()
            ts_name = (ts.get('description') or '').strip()


            if ts_barcode:
                set_if_has_track('barcode', ts_barcode)  # <-- важливо

            if ts_sku:
                set_if_has_track('sku', ts_sku)  # <-- важливо

            if ts_name:
                set_if_has_track('name', ts_name)  # <-- важливо
            #
            # if ts_barcode:
            #     set_if_has(obj, 'barcode', ts_barcode, changes)
            # if ts_sku:
            #     set_if_has(obj, 'sku', ts_sku, changes)
            # if ts_name:
            #     set_if_has(obj, 'name', ts_name, changes)

            # 2) money поля (Decimal, 2 знаки) + кількість
            # set_if_has(obj, 'prime_cost',                 money(ts.get('prime_cost')), changes)
            set_if_has(obj, 'retail_price',               money(ts.get('wholesale_price')), changes)
            # set_if_has(obj, 'wholesale_price',            money(ts.get('wholesale_price')), changes)
            # set_if_has(obj, 'retail_price_with_discount', money(ts.get('retail_price_with_discount')), changes)
            set_if_has(obj, 'warehouse_quantity',         as_int(ts.get('warehouse_quantity')), changes)

            # 2.x) визначаємо "На вагу" по producer_collection_full
            ts_prod_coll = (ts.get('good_type_full') or '').strip()
            tokens = [t.strip().lower() for t in ts_prod_coll.split(',') if t.strip()]
            is_weighted = any(t == 'на вагу' for t in tokens) or ('на вагу' in ts_prod_coll.lower())
            self.stdout.write(f"good_type_full={ts_prod_coll} → tokens={tokens} → is_weighted={is_weighted}")

            # якщо вагова -> 0, якщо ні -> None (порожньо)
            target_bag = Decimal('0') if is_weighted else None

            # встановлюємо для Product і для Variant (поле є в обох)
            set_if_has(obj, 'original_bag_weight_kg', target_bag, changes)

            # 3) Примусова перебудова slug, якщо потрібно
            if need_slug and hasattr(obj, 'rebuild_slug'):
                obj.rebuild_slug()
                changes.append(('slug', old_slug, getattr(obj, 'slug', None)))

            if changes:
                ident = getattr(obj, 'torgsoft_id', None) or getattr(obj, 'id', None)
                preview.append(
                    f"[{label}] id={ident}: " +
                    ", ".join(f"{f} {old} → {new}" for f, old, new in changes)
                )
                if not dry:
                    obj.save()
                updated_cnt += 1

        @transaction.atomic
        def sync_all():
            if not only_variants:
                for p in Product.objects.all():
                    sync_obj(p, 'Product')
            if not only_products:
                for v in Product_Variant.objects.all():
                    sync_obj(v, 'Variant')

        sync_all()

        for line in preview[:400]:
            self.stdout.write(line)
        if len(preview) > 400:
            self.stdout.write(f"... та ще {len(preview)-400} змін")

        self.stdout.write(self.style.SUCCESS(
            f"Готово: оновлено обʼєктів = {updated_cnt}{' (dry-run)' if dry else ''}"
        ))
