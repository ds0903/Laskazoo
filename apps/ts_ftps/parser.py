import csv, io, re
from decimal import Decimal, InvalidOperation
from django.conf import settings

# мапа CSV-заголовок -> ім'я поля моделі
HEADER_MAP = {
    "GoodID": "good_id",
    "GoodName": "good_name",
    "Description": "description",
    "Country": "country",
    "Articul": "articul",
    "RetailPrice": "retail_price",
    "WholesalePrice": "wholesale_price",
    "RetailPriceWithDiscount": "retail_price_with_discount",
    "MinQuantityForOrder": "min_quantity_for_order",
    "Height": "height",
    "Width": "width",
    "Category": "category",
    "WarehouseQuantity": "warehouse_quantity",
    "Display": "display",
    "TheSize": "the_size",
    "Color": "color",
    "Material": "material",
    "FashionName": "fashion_name",
    "Sex": "sex",
    "ShortName": "short_name",
    "GoodTypeFull": "good_type_full",
    "ProducerCollectionFull": "producer_collection_full",
    "Season": "season",
    "Barcode": "barcode",
    "Pack": "pack",
    "PackSize": "pack_size",
    "PowerSupply": "power_supply",
    "CountUnitsPerBox": "count_units_per_box",
    "Age": "age",
    "Measure": "measure",
    "MeasureUnit": "measure_unit",
    "Closeout": "closeout",
    "RetailPricePerUnit": "retail_price_per_unit",
    "WholesalePricePerUnit": "wholesale_price_per_unit",
    "EqualSalePrice": "equal_sale_price",
    "EqualWholesalePrice": "equal_wholesale_price",
    "EqualCurrencyName": "equal_currency_name",
    "PrimeCost": "prime_cost",
    "SupplierCode": "supplier_code",
    "Analogs": "analogs",
    "new_description" :"new_description",
}

NUMERIC_FIELDS = {
    "retail_price","wholesale_price","retail_price_with_discount",
    "min_quantity_for_order","height","width","warehouse_quantity",
    "retail_price_per_unit","wholesale_price_per_unit",
    "equal_sale_price","equal_wholesale_price","prime_cost",
}
INT_FIELDS = {"count_units_per_box"}
BOOL_FIELDS = {"closeout"}

def _to_decimal(x, default="0"):
    s = str(x or "").strip().replace(" ", "").replace(",", ".")
    if s == "": s = str(default)
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal(str(default))

def _to_int(x):
    try:
        return int(float(str(x).replace(",", ".").strip()))
    except Exception:
        return 0

def _to_bool(x):
    s = str(x or "").strip().lower()
    return s in {"1","true","yes","так","y","t","да","истина"}

def sniff_delimiter(text):
    force = settings.TS_SYNC["FILE"].get("DELIMITER", "auto")
    if force != "auto":
        return {";":";", ",":",", "\\t":"\t", "|":"|"}.get(force, ";")
    sample = text[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,|\t").delimiter
    except Exception:
        return ";"

def parse_rows(raw_bytes):
    enc = settings.TS_SYNC["FILE"].get("ENCODING", "utf-8")
    text = raw_bytes.decode(enc, errors="replace")
    delim = sniff_delimiter(text)
    rdr = csv.DictReader(io.StringIO(text), delimiter=delim)
    for row in rdr:
        data = {}
        for hdr, val in row.items():
            if hdr is None:
                continue
            key = HEADER_MAP.get(hdr.strip())
            if not key:
                continue
            if key in NUMERIC_FIELDS:
                data[key] = _to_decimal(val)
            elif key in INT_FIELDS:
                data[key] = _to_int(val)
            elif key in BOOL_FIELDS:
                data[key] = _to_bool(val)
            else:
                data[key] = (val or "").strip()
        # вимагаємо принаймні good_id
        if data.get("good_id"):
            yield data
