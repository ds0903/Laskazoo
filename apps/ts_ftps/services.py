import os
from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction  # <-- додали
from .utils import get_reader
from .parser import parse_rows
from .models import TSGoods  # якщо сирі дані пишемо у свою таблицю

def get_product_model():
    """
    Якщо ти ще хочеш імпортувати в свою модель Product (не сирі дані),
    вкажи TS_PRODUCT_MODEL у settings. Інакше можеш не використовувати цю частину.
    """
    label = settings.TS_SYNC.get("PRODUCT_MODEL", "ts_sftp.Product")
    return apps.get_model(label)

def upsert_products(items, photos_reader=None, photos_dir=None):
    """
    Варіант імпорту у твою модель Product (НЕ обов’язково). Залишив, раптом треба.
    """
    Product = get_product_model()
    upserted = 0
    for it in items:
        defaults = dict(
            sku=it.get("sku"),
            barcode=it.get("barcode"),
            name=it.get("name"),
            qty=it.get("qty"),
            retail_price=it.get("retail_price"),
            wholesale_price=it.get("wholesale_price"),
            description=it.get("description"),
            is_active=True,
        )
        obj, _ = Product.objects.update_or_create(
            external_id=str(it["external_id"]),
            defaults=defaults
        )

        # фото (опціонально)
        photo_name = (it.get("photo") or "").strip()
        if photos_reader and photo_name:
            photo_name = photo_name.replace("\\", "/").split("/")[-1]
            remote = f"{photos_dir.rstrip('/')}/{photo_name}"
            try:
                img = photos_reader.read_bytes(remote)
            except Exception:
                img = None
            if img:
                rel = f"products/{obj.external_id}_{photo_name}"
                default_storage.save(rel, ContentFile(img))
                if hasattr(obj, "image"):
                    obj.image.name = rel
                    obj.save(update_fields=["image"])
        upserted += 1
    return upserted

def import_from_source():
    """
    Якщо потрібно імпортувати у свою модель Product (НЕ сирі дані).
    """
    mode, sftp, incoming_dir, photos_dir, file_name = get_reader()
    trs_path = f"{incoming_dir.rstrip('/')}/{file_name}"

    if mode == "sftp":
        raw = sftp.read_bytes(trs_path)
        items = list(parse_rows(raw))  # <-- робимо список (інакше немає len)
        upserted = upsert_products(items, photos_reader=sftp, photos_dir=photos_dir)
    else:
        local = os.path.join(incoming_dir, file_name)
        with open(local, "rb") as f:
            raw = f.read()
        items = list(parse_rows(raw))
        upserted = upsert_products(items, photos_reader=None, photos_dir=None)

    return {"total": len(items), "upserted": upserted}

@transaction.atomic
def import_ts_goods(mode: str = 'upsert'):
    """
    mode:
      - 'upsert'  (за замовч.) update_or_create по good_id
      - 'replace' видалити всі рядки і залити з файлу
      - 'append'  тільки створювати нові, існуючі пропускати
    """
    mode = mode.lower().strip()
    if mode not in {'upsert', 'replace', 'append'}:
        mode = 'upsert'

    # 1) зчитати файл (ftp/ftps/local)
    source_mode, client, incoming_dir, _photos_dir, file_name = get_reader()
    trs_path = f"{incoming_dir.rstrip('/')}/{file_name}"

    if source_mode in ("ftp", "ftps"):
        raw = client.read_bytes(trs_path)
    else:
        with open(os.path.join(incoming_dir, file_name), "rb") as f:
            raw = f.read()

    # 2) розпарсити всі рядки одразу (щоб мати total)
    items = [dict(r) for r in parse_rows(raw)]  # копії dict на всякий
    total = len(items)
    created = updated = skipped = 0

    # 3) режими
    if mode == 'replace':
        # повна заміна
        TSGoods.objects.all().delete()
        objs = []
        for rec in items:
            rec = dict(rec)
            good_id = str(rec.pop("good_id"))
            objs.append(TSGoods(good_id=good_id, **rec))
        if objs:
            TSGoods.objects.bulk_create(objs, batch_size=1000)
        created = len(objs)
        return {"total": total, "created": created, "updated": 0, "skipped": 0}

    if mode == 'append':
        # лише створюємо; існуючі з таким good_id пропускаємо
        for rec in items:
            rec = dict(rec)
            good_id = str(rec.pop("good_id"))
            obj, was_created = TSGoods.objects.get_or_create(good_id=good_id, defaults=rec)
            if was_created:
                created += 1
            else:
                skipped += 1
        return {"total": total, "created": created, "updated": 0, "skipped": skipped}

    # upsert (оновити або створити)
    for rec in items:
        rec = dict(rec)

        good_id = str(rec.pop("good_id", "")).strip()
        if not good_id:
            # якщо раптом попався пустий good_id — пропускаємо
            continue

        # ВАЖЛИВО: не даємо Django вставити чужий PK
        safe_defaults = {k: v for k, v in rec.items() if k not in ("id", "pk")}

        obj, was_created = TSGoods.objects.update_or_create(
            good_id=good_id,
            defaults=safe_defaults,
        )

        if was_created:
            created += 1
        else:
            updated += 1

    return {"total": total, "created": created, "updated": updated, "skipped": 0}
