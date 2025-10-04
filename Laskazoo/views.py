from apps.products.models import PopularProduct, Product_Variant, PopularCategory
from apps.favourites.models import Favourite
from apps.manager.models import Banner
from django.shortcuts import render, redirect

def stores_map(request):
    stores = [
        {
            "id": 1,
            "city": "Боярка",
            "name": "Ласка — Боярка",
            "addr": "вулиця Шевченка, Боярка, Київська область, 08151",
            "hours": "10:00–21:00",
            "phone": "+380 63 239 2711",
            "lat": 50.3437026, "lng": 30.3015502,
        },
        {
            "id": 2,
            "city": "Київ",
            "name": "Ласка — Київ",
            "addr": "вулиця Академіка Булаховського, 5Д, Київ, 02000",
            "hours": "10:00–22:00",
            "phone": "+380 00 000 00 00",
            "lat": 50.4694751, "lng": 30.3366752,
        },
        {

            "id": 3,
            "city": "Ірпінь",
            "name": "Ласка — Ірпінь",
            "addr": "вулиця Літературна, 14д, Ірпінь, Київська область, 08205",
            "hours": "10:00–21:00",
            "phone": "+380 93 265 2481",
            "lat": 50.509580, "lng": 30.232698,
        },

        {
            "id": 4,
            "city": "Боярка",
            "name": "Ласка — Боярка",
            "addr": "вулиця Садова, 3, Боярка, Київська область, 08150",
            "hours": "10:00–21:00",
            "phone": "+380 63 071 3538",
            "lat": 50.318296, "lng": 30.2979583,
        },

        {
            "id": 5,
            "city": "Київ",
            "name": "Ласка — Київ",
            "addr": "вулиця Героїв Дніпра, Київ, 02000",
            "hours": "10:00–21:00",
            "phone": "+380 93 204 8162",
            "lat": 50.523632, "lng": 30.500066,
        },

        {
            "id": 6,
            "city": "Київ",
            "name": "Ласка — Київ",
            "addr": "вулиця Авіаконструктора Антонова, 35, Київ, 02000",
            "hours": "10:00–21:00",
            "phone": "+380 93 204 8162",
            "lat": 50.4311115, "lng": 30.4539739,
        },

    ]
    return render(request, 'zoosvit/core/map.html', {"stores": stores})

def home(request):
    # Банери для карусел головної сторінки
    banners = Banner.objects.filter(is_active=True).order_by('position', '-created_at')[:4]
    
    populars = (
       PopularProduct.objects
       .select_related('product', 'product__brand', 'product__category')
       .order_by('position')
       .filter(is_active=True, product__is_active=True)
    )[:20]

    popular_cats = (
        PopularCategory.objects
        .filter(is_active=True)
        .select_related('category__main_category')
        .order_by('position', '-created_at')[:18]
    )

    product_ids = [pp.product_id for pp in populars]
    variants = (Product_Variant.objects
                .filter(product_id__in=product_ids)
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


PAGES = {
    "public-offer": {
        "title": "Договір публічної оферти",
        "date":  "10.03.2025",
        "body": """
<h3>ПУБЛІЧНА ОФЕРТА</h3>
<p>Цей договір є офіційною та публічною пропозицією Продавця укласти договір купівлі-продажу товару дистанційно...</p>

<h4>Терміни</h4>
<ol>
  <li><strong>Акцепт</strong> — повне прийняття та виконання умов Договору.</li>
  <li><strong>Продавець</strong> — ТОВ «Зоосвіт» ...</li>
  <li><strong>Покупець</strong> — фізична/юридична особа, що оформляє Замовлення...</li>
</ol>

<h4>Порядок оформлення замовлення</h4>
<p>Покупець оформлює замовлення на сайті, після чого отримує підтвердження на e-mail або у кабінеті...</p>

<h4>Оплата та доставка</h4>
<p>Оплата здійснюється готівкою при отриманні або безготівково; доставка виконується службами доставки...</p>
""",
    },
    "payment-delivery": {
        "title": "Оплата та доставка",
        "date":  "10.03.2025",
        "body": """
<h3>Оплата</h3>
<ul>
  <li>Готівкою при отриманні</li>
  <li>Банківською картою онлайн</li>
  <li>Безготівковий розрахунок для юр. осіб</li>
</ul>
<h3>Доставка</h3>
<p>Курʼєром по Києву, Новою поштою по Україні, самовивіз з магазинів Зоосвіт.</p>
""",
    },
    "returns": {
        "title": "Обмін та повернення",
        "date":  "10.03.2025",
        "body": """
<p>Повернення/обмін можливий протягом 14 днів згідно Закону України «Про захист прав споживачів», за умови
збереження товарного вигляду, пломб і чеку. Витрати на пересилання — за рахунок Покупця, якщо інше не передбачено законом.</p>
""",
    },
    "privacy": {
        "title": "Політика конфіденційності",
        "date":  "10.03.2025",
        "body": """
<p>Ми обробляємо персональні дані з метою надання послуг, виконання замовлень та маркетингових розсилок за згодою користувача.
Дані зберігаються належним чином і не передаються третім особам, окрім випадків, передбачених законом.</p>
""",
    },
    "contacts": {
        "title": "Контакти",
        "date":  "10.03.2025",
        "body": """
<div class="contacts-info">
  <div class="contact-section">
    <h3>📞 Контактна інформація</h3>
    <div class="contact-item">
      <strong>Телефон:</strong> <a href="tel:+380932384730">+38 093 238 47 30</a>
    </div>
    <div class="contact-item">
      <strong>E-mail:</strong> <a href="mailto:zoosvitoffice15@gmail.com">zoosvitoffice15@gmail.com</a>
    </div>
    <div class="contact-item">
      <strong>Telegram:</strong> <a href="https://t.me/ds0903" target="_blank">@ds0903</a>
    </div>
    <div class="contact-item">
      <strong>Графік роботи:</strong> Пн–Нд, 9:00 – 20:00
    </div>
  </div>
</div>

<style>
.contacts-info { max-width: 600px; margin: 0 auto; }
.contact-section { background: #f8f9fa; padding: 2rem; border-radius: 10px; }
.contact-section h3 { color: var(--color-primary); margin-bottom: 1.5rem; font-size: 1.5rem; text-align: center; }
.contact-item { margin-bottom: 1rem; padding: 0.75rem; background: #fff; border-radius: 6px; text-align: center; }
.contact-item strong { color: #333; display: block; margin-bottom: 0.25rem; }
.contact-item a { color: var(--color-primary); text-decoration: none; font-size: 1.1rem; }
.contact-item a:hover { text-decoration: underline; }
</style>
""",
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