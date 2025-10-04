// compact-spacing.js - миттєве застосування компактного макету
(function() {
    'use strict';
    
    // Швидке застосування компактного макету одразу після завантаження DOM
    function applyCompactSpacing() {
        const body = document.body;
        const path = window.location.pathname;
        
        // Визначаємо тип сторінки
        const isCatalogPage = path === '/categories/' || path.includes('/catalog');
        const isCategoryPage = path.includes('/categories/') && path !== '/categories/';
        
        if (isCatalogPage) {
            body.classList.add('catalog-page');
            body.classList.remove('category-page');
        } else if (isCategoryPage) {
            body.classList.add('category-page');
            body.classList.remove('catalog-page');
        }
        
        // Знаходимо сітки та підраховуємо картки
        const grids = document.querySelectorAll('.product-grid, .subcategory-grid, .main-category-grid');
        
        grids.forEach(grid => {
            const cards = grid.querySelectorAll('.prod-card, .subcategory-card, .category-card');
            const cardCount = cards.length;
            
            // Миттєво додаємо атрибут з кількістю карток
            grid.setAttribute('data-card-count', cardCount);
            
            // Прибираємо всі попередні класи та додаємо новий
            grid.classList.remove('cards-1-row', 'cards-2-rows', 'cards-3-rows', 'cards-4-5-rows', 'cards-many-rows');
            
            if (cardCount <= 4) {
                grid.classList.add('cards-1-row');
            } else if (cardCount <= 8) {
                grid.classList.add('cards-2-rows');
            } else if (cardCount <= 12) {
                grid.classList.add('cards-3-rows');
            } else if (cardCount <= 20) {
                grid.classList.add('cards-4-5-rows');
            } else {
                grid.classList.add('cards-many-rows');
            }
        });
        
        // Застосовуємо спеціальні стилі для зменшення відступів
        if (isCatalogPage || isCategoryPage) {
            // Основний контент
            const siteMain = document.querySelector('.site-main');
            if (siteMain) {
                siteMain.style.paddingBottom = '5px';
                siteMain.style.minHeight = 'auto';
            }
            
            // Заголовки та навігація
            const elements = [
                { selector: '.catalog-page-heading', styles: { marginBottom: '8px' } },
                { selector: '.breadcrumbs', styles: { marginBottom: '5px', paddingBottom: '2px' } },
                { selector: '.top-cats-bar', styles: { marginBottom: '5px' } },
                { selector: '.catalog-controls', styles: { marginBottom: '8px' } },
                { selector: '.catalog-header', styles: { marginBottom: '8px' } },
                { selector: '.category-nav', styles: { marginBottom: '8px' } },
                { selector: '.pagination-wrapper', styles: { marginTop: '5px', marginBottom: '5px' } }
            ];
            
            elements.forEach(({ selector, styles }) => {
                const element = document.querySelector(selector);
                if (element) {
                    Object.assign(element.style, styles);
                }
            });
        }
    }
    
    // Застосовуємо миттєво, як тільки DOM готовий
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyCompactSpacing);
    } else {
        applyCompactSpacing();
    }
    
    // Також застосовуємо при зміні розміру вікна
    window.addEventListener('resize', function() {
        clearTimeout(this.resizeTimer);
        this.resizeTimer = setTimeout(applyCompactSpacing, 100);
    });
    
})();
