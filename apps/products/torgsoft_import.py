# apps/products/services/torgsoft_import.py
import os
from decimal import Decimal
from django.db import transaction
from django.utils.text import slugify
from django.conf import settings
from apps.ts_ftps.ftp_client import get_reader
from apps.ts_ftps.parser import parse_rows
from models import Product, Product_Variant, Category, Brand, Main_Categories
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def _slug_unique(base: str) -> str:
    s = slugify(base)[:200] or "tovar"
    uniq = s
    i = 2
    while Product.objects.filter(slug=uniq).exists():
        uniq = f"{s}-{i}"
        i += 1
    return uniq

def _get_or_create_category(full_name: str) -> Category:
    # приклад: спробуємо покласти все в один main_category "Інше"
    if not full_name:
        full_name = "Інше"
    main, _ = Main_Categories.objects.get_or_create(
        slug="inshe", defaults={"name": "Інше"}
    )
    slug = slugify(full_name)[:200] or "kategoria"
    cat, created = Category.objects.get_or_create(
        slug=slug,
        defaults={"name": full_name, "main_category": main}
    )
    return cat

def _get_or_create_brand(name: str) -> Brand:
    if not name:
        name = "No-name"
    brand_slug = slugify(name)[:200]
    brand, _ = Brand.objects.get_or_create(
        brand_slug=brand_slug,
        defaults={"name": name, "country_slug":"-", "country":"-"}
    )
    return brand

def _save_photo_to_product(prod: Product, photo_reader, remote_dir, filename):
    if not photo_reader or not filename:
        return
    filename = filename.replace("\\", "/").split("/")[-1]
    remote = f"{remote_dir.rstrip('/')}/{filename}"
    try:
        img = photo_reader.read_bytes(remote)
    except Exception:
        img = None
    if img:
        rel = f"products/{prod.slug}_{filename}"
        default_storage.save(rel, ContentFile(img))
        prod.image.name = rel
        prod.save(update_fields=["image"])

@transaction.atomic
def import_products_variants_from_trs():
    mode, sftp, incoming_dir, photos_dir, file_name = get_reader()
    trs_path = f"{incoming_dir.rstrip('/')}/{file_name}"

    # 1) читаємо файл
    raw = sftp.read_bytes(trs_path) if mode == "sftp" else open(trs_path, "rb").read()
    rows = parse_rows(raw)  # список dict, у яких МОЖУТЬ бути ключі: parent_id, variant_id, name, sku, barcode, retail_price, qty, brand, category, photo, weight, size, color, characteristic

    # 2) нормалізуємо: намагаємося вийняти parent_id/variant_id з полів, що прийшли
    def get_parent_id(r):
        return str(r.get("parent_id") or r.get("external_id") or r.get("id") or "")
    def get_variant_id(r):
        return str(r.get("variant_id") or r.get("barcode") or r.get("sku") or "")

    upserted_products = 0
    upserted_variants = 0

    for r in rows:
        parent_id = get_parent_id(r)
        variant_id = get_variant_id(r)
        name = r.get("name") or "Товар"

        # 2.1 Категорія/бренд
        category = _get_or_create_category(r.get("category") or "")
        brand = _get_or_create_brand(r.get("brand") or "")

        # 2.2 Продукт (база)
        prod = None
        if parent_id:
            prod = Product.objects.filter(external_id=parent_id).first()
        if not prod:
            prod = Product.objects.filter(name=name, brand=brand, category=category).first()

        if not prod:
            prod = Product(
                name=name,
                slug=_slug_unique(name),
                sku=r.get("sku") or "",
                retail_price=Decimal(r.get("retail_price") or "0"),
                category=category,
                brand=brand,
                description=r.get("description") or "",
                external_id=parent_id or None,
            )
            prod.save()
            upserted_products += 1
        else:
            # оновлюємо базові поля (без ціни — ціна буде на варіанті)
            changed = False
            if not prod.external_id and parent_id:
                prod.external_id = parent_id
                changed = True
            new_desc = r.get("description") or prod.description
            if prod.description != new_desc:
                prod.description = new_desc
                changed = True
            if changed:
                prod.save()

        # 2.3 Фото на базовому товарі (опц.)
        photo_name = r.get("photo")
        if photos_dir and photo_name and not prod.image:
            _save_photo_to_product(prod, sftp if mode=="sftp" else None, photos_dir, photo_name)

        # 2.4 Варіант
        sku = r.get("sku") or variant_id or ""
        weight = r.get("weight")
        size   = r.get("size")
        color  = r.get("color")
        qty    = r.get("qty") or 0
        retail_price  = r.get("retail_price") or 0

        v_qs = Product_Variant.objects.filter(product=prod)
        if variant_id:
            v = v_qs.filter(external_id=variant_id).first()
        else:
            # fallback — шукаємо по sku
            v = v_qs.filter(sku=sku).first()

        if not v:
            v = Product_Variant(
                product=prod,
                sku=sku[:255],
                retail_price=Decimal(str(retail_price)),
                weight=Decimal(str(weight or 0)),
                stock=int(qty),
                size=(str(size) if size else None),
                color=(str(color) if color else None),
                external_id=variant_id or None,
            )
            v.save()
            upserted_variants += 1
        else:
            changed = False
            new_price = Decimal(str(retail_price))
            new_weight = Decimal(str(weight or 0))
            new_stock = int(qty)
            if v.retail_price != new_price:
                v.retail_price = new_price; changed = True
            if v.weight != new_weight:
                v.weight = new_weight; changed = True
            if v.warehouse_quantity != new_stock:
                v.warehouse_quantity = new_stock; changed = True
            if size and v.size != str(size):
                v.size = str(size); changed = True
            if color and v.color != str(color):
                v.color = str(color); changed = True
            if not v.external_id and variant_id:
                v.external_id = variant_id; changed = True
            if changed:
                v.save()

    return {"products": upserted_products, "variants": upserted_variants, "rows": len(rows)}
