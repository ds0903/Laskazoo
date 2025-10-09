import os
from apps.products.models import PopularProduct, Product_Variant, PopularCategory
from apps.favourites.models import Favourite
from apps.manager.models import Banner
from django.shortcuts import render, redirect
from django.conf import settings

# def stores_map(request):
#     stores = [
#         {
#             "id": 1,
#             "city": "Боярка",
#             "name": "Ласка — Боярка",
#             "addr": "вулиця Шевченка, Боярка, Київська область, 08151",
#             "hours": "10:00–21:00",
#             "phone": "+380 63 239 2711",
#             "lat": 50.3437026, "lng": 30.3015502,
#         },
#         {
#             "id": 2,
#             "city": "Київ",
#             "name": "Ласка — Київ",
#             "addr": "вулиця Академіка Булаховського, 5Д, Київ, 02000",
#             "hours": "10:00–22:00",
#             "phone": "+380 00 000 00 00",
#             "lat": 50.4694751, "lng": 30.3366752,
#         },
#         {
#
#             "id": 3,
#             "city": "Ірпінь",
#             "name": "Ласка — Ірпінь",
#             "addr": "вулиця Літературна, 14д, Ірпінь, Київська область, 08205",
#             "hours": "10:00–21:00",
#             "phone": "+380 93 265 2481",
#             "lat": 50.509580, "lng": 30.232698,
#         },
#
#         {
#             "id": 4,
#             "city": "Боярка",
#             "name": "Ласка — Боярка",
#             "addr": "вулиця Садова, 3, Боярка, Київська область, 08150",
#             "hours": "10:00–21:00",
#             "phone": "+380 63 071 3538",
#             "lat": 50.318296, "lng": 30.2979583,
#         },
#
#         {
#             "id": 5,
#             "city": "Київ",
#             "name": "Ласка — Київ",
#             "addr": "вулиця Героїв Дніпра, Київ, 02000",
#             "hours": "10:00–21:00",
#             "phone": "+380 93 204 8162",
#             "lat": 50.523632, "lng": 30.500066,
#         },
#
#         {
#             "id": 6,
#             "city": "Київ",
#             "name": "Ласка — Київ",
#             "addr": "вулиця Авіаконструктора Антонова, 35, Київ, 02000",
#             "hours": "10:00–21:00",
#             "phone": "+380 93 204 8162",
#             "lat": 50.4311115, "lng": 30.4539739,
#         },
#
#     ]
#     return render(request, 'zoosvit/core/map.html', {"stores": stores})

def home(request):
    # Банери для карусел головної сторінки
    banners = Banner.objects.filter(is_active=True).order_by('position', '-created_at')[:4]
    
    # Популярні товари - показуємо тільки активні
    populars = (
       PopularProduct.objects
       .select_related('product', 'product__brand', 'product__category')
       .order_by('position')
       .filter(is_active=True, product__is_active=True)
    )[:20]

    # Популярні категорії - показуємо тільки активні
    popular_cats = (
        PopularCategory.objects
        .filter(is_active=True, category__is_active=True)
        .select_related('category__main_category')
        .order_by('position', '-created_at')[:18]
    )

    product_ids = [pp.product_id for pp in populars]
    # Варіанти товарів - показуємо тільки активні
    variants = (Product_Variant.objects
                .filter(product_id__in=product_ids, is_active=True)
                .only('id', 'product_id', 'sku', 'retail_price', 'weight', 'size', 'image', 'warehouse_quantity')
                .order_by('retail_price'))

    by_pid = {}
    for v in variants:
        by_pid.setdefault(v.product_id, []).append(v)


    for pp in populars:
        pp.product.variants_for_card = by_pid.get(pp.product_id, [])

    if request.user.is_authenticated:
        fav_variant_ids = set(
            Favourite.objects.filter(user=request.user, variant__isnull=False)
            .values_list('variant_id', flat=True)
        )
        fav_product_ids = set(
            Favourite.objects.filter(user=request.user, variant__isnull=True)
            .values_list('product_id', flat=True)
        )
    else:
        fav_variant_ids = set(map(int, request.session.get('fav_variant_ids', [])))
        fav_product_ids = set(map(int, request.session.get('fav_product_ids', [])))

    return render(request, 'zoosvit/core/home.html', {
        'banners': banners,
        'populars': populars,
        'fav_variant_ids': list(fav_variant_ids),
        'fav_product_ids': list(fav_product_ids),
        'popular_cats': popular_cats,
    })


# Читаємо текст договору оферти з окремого файлу
PUBLIC_OFFER_CONTENT = ""
try:
    offer_file_path = os.path.join(settings.BASE_DIR, 'public_offer_content.txt')
    with open(offer_file_path, 'r', encoding='utf-8') as f:
        PUBLIC_OFFER_CONTENT = f.read()
except Exception as e:
    PUBLIC_OFFER_CONTENT = "<p>Договір публічної оферти тимчасово недоступний. Будь ласка, зверніться до служби підтримки.</p>"

# Читаємо текст політики конфіденційності з окремого файлу
PRIVACY_CONTENT = ""
try:
    privacy_file_path = os.path.join(settings.BASE_DIR, 'privacy.txt')
    with open(privacy_file_path, 'r', encoding='utf-8') as f:
        PRIVACY_CONTENT = f.read()
except Exception as e:
    PRIVACY_CONTENT = "<p>Договір політики конфідеціальності тимчасово недоступний. Будь ласка, зверніться до служби підтримки.</p>"

# Читаємо текст оплати та доставки з окремого файлу
PAYMENT_DELIVERY_CONTENT = ""
try:
    payment_file_path = os.path.join(settings.BASE_DIR, 'payment_delivery_content.txt')
    with open(payment_file_path, 'r', encoding='utf-8') as f:
        PAYMENT_DELIVERY_CONTENT = f.read()
except Exception as e:
    PAYMENT_DELIVERY_CONTENT = "<p>Інформація про оплату та доставку тимчасово недоступна. Будь ласка, зверніться до служби підтримки.</p>"

# Читаємо текст обміну та повернення з окремого файлу
RETURNS_CONTENT = ""
try:
    returns_file_path = os.path.join(settings.BASE_DIR, 'returns_content.txt')
    with open(returns_file_path, 'r', encoding='utf-8') as f:
        RETURNS_CONTENT = f.read()
except Exception as e:
    RETURNS_CONTENT = "<p>Інформація про обмін та повернення тимчасово недоступна. Будь ласка, зверніться до служби підтримки.</p>"

# Читаємо текст контактів з окремого файлу
CONTACTS_CONTENT = ""
try:
    contacts_file_path = os.path.join(settings.BASE_DIR, 'contacts_content.txt')
    with open(contacts_file_path, 'r', encoding='utf-8') as f:
        CONTACTS_CONTENT = f.read()
except Exception as e:
    CONTACTS_CONTENT = "<p>Контактна інформація тимчасово недоступна. Будь ласка, спробуйте пізніше.</p>"

PAGES = {
    "public-offer": {
        "title": "Договір публічної оферти",
        "date":  "07.10.2025",
        "body": PUBLIC_OFFER_CONTENT,
    },
    "payment-delivery": {
        "title": "Оплата та доставка",
        "date":  "07.10.2025",
        "body": PAYMENT_DELIVERY_CONTENT,
    },
    "returns": {
        "title": "Обмін та повернення",
        "date":  "07.10.2025",
        "body": RETURNS_CONTENT,
    },
    "privacy": {
        "title": "Політика конфіденційності",
        "date":  "07.10.2025",
        "body": PRIVACY_CONTENT,
    },
    "contacts": {
        "title": "Контакти",
        "date":  "07.10.2025",
        "body": CONTACTS_CONTENT,
    },
}

LEFT_NAV = [
    ("public-offer",     "Договір публічної оферти"),
    ("payment-delivery", "Оплата та доставка"),
    ("returns",          "Обмін та повернення"),
    ("privacy",          "Політика конфіденційності"),
    ("contacts",         "Контакти"),
]

def info_page(request, slug: str):
    page = PAGES.get(slug)
    if not page:
        return redirect('info_page', slug='public-offer')
    return render(request, 'zoosvit/core/info_page.html', {
        "page": page,
        "left_nav": LEFT_NAV,
        "active": slug,
    })
