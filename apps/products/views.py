# apps/products/views.py
from django.shortcuts import render, get_object_or_404
from .models import Main_Categories, Category, Product, Brand
from django.db.models import Count

def main_category_list(request):
    mains = Main_Categories.objects.all()
    return render(request, 'zoosvit/products/main_category_list.html', {
        'mains': mains,
    })


def subcategory_list(request, main_slug):
    main = get_object_or_404(Main_Categories, slug=main_slug)
    subs = main.categories.all()
    return render(request, 'zoosvit/products/subcategory_list.html', {
        'main':       main,
        'categories': subs,
    })


def category_list(request, main_slug, slug):
    category = get_object_or_404(
        Category,
        slug=slug,
        main_category__slug=main_slug
    )

    qs = Product.objects.filter(category=category)

    brands = Brand.objects.annotate(count=Count('products'))
    return render(request, 'zoosvit/products/category_list.html', {
        'main':     category.main_category,   # за бажанням
        'category': category,
        'products': qs,
        'brands':   brands,
        # …
    })

def product_detail(request, main_slug, slug, product_slug):
    # 1) перевіряємо, що категорія належить до головної
    category = get_object_or_404(
        Category,
        slug=slug,
        main_category__slug=main_slug
    )
    # 2) тягнемо сам товар
    product = get_object_or_404(
        Product,
        slug=product_slug,
        category=category
    )

    variants = product.variants.all()

    return render(request, 'zoosvit/products/product_detail.html', {
        'main_slug': main_slug,
        'category':  category,
        'product':   product,
        'variants':  variants
    })
