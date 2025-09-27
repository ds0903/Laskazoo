// ultra-compact.js - миттєве прибирання порожнього простору
(function() {
    'use strict';
    
    function forceUltraCompact() {
        const path = window.location.pathname;
        const isCatalogPage = path === '/categories/' || path.includes('/catalog') || path.includes('/categories/');
        
        if (!isCatalogPage) return;
        
        // Додаємо класи до body
        document.body.classList.add('ultra-compact');
        
        // Агресивне прибирання відступів
        const elementsToCompact = [
            '.site-main',
            '.catalog.container', 
            '.catalog-wrapper',
            '.catalog-main',
            '.product-grid',
            '.pagination-wrapper',
            '.catalog-page-heading',
            '.breadcrumbs',
            '.top-cats-bar',
            '.catalog-controls',
            '.catalog-header',
            '.category-nav'
        ];
        
        elementsToCompact.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.marginBottom = '0';
                el.style.paddingBottom = '0';
                el.style.minHeight = 'auto';
            });
        });
        
        // Спеціально для пагінації - розміщуємо максимально близько
        const paginationWrapper = document.querySelector('.pagination-wrapper');
        if (paginationWrapper) {
            paginationWrapper.style.marginTop = '5px';
            paginationWrapper.style.marginBottom = '5px';
            paginationWrapper.style.paddingTop = '0';
            paginationWrapper.style.paddingBottom = '0';
        }
        
        // Сітка продуктів
        const productGrid = document.querySelector('.product-grid');
        if (productGrid) {
            productGrid.style.marginBottom = '5px';
            productGrid.style.paddingBottom = '0';
            
            // Підраховуємо кількість карток
            const cards = productGrid.querySelectorAll('.prod-card');
            const cardCount = cards.length;
            
            // Застосовуємо спеціальні відступи залежно від кількості
            if (cardCount <= 5) {
                productGrid.style.marginBottom = '3px';
            } else if (cardCount <= 8) {
                productGrid.style.marginBottom = '5px';
            } else {
                productGrid.style.marginBottom = '8px';
            }
        }
        
        // Прибираємо відступи з site-main
        const siteMain = document.querySelector('.site-main');
        if (siteMain) {
            siteMain.style.paddingBottom = '0';
            siteMain.style.marginBottom = '0';
            siteMain.style.minHeight = 'auto';
        }
        
        // Footer - мінімальний відступ
        const footer = document.querySelector('footer');
        if (footer) {
            footer.style.marginTop = '5px';
            footer.style.paddingTop = '15px';
        }
        
        // Прибираємо зайві відступи з усіх section
        const sections = document.querySelectorAll('.site-main section, .site-main .container');
        sections.forEach(section => {
            section.style.marginBottom = '0';
            section.style.paddingBottom = '0';
        });
        
        // Спеціально для останнього елемента
        const lastElement = document.querySelector('.site-main > *:last-child');
        if (lastElement) {
            lastElement.style.marginBottom = '0';
            lastElement.style.paddingBottom = '0';
        }
    }
    
    // Застосовуємо миттєво
    const applyNow = () => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', forceUltraCompact);
        } else {
            forceUltraCompact();
        }
        
        // Також після завантаження всього контенту
        window.addEventListener('load', forceUltraCompact);
    };
    
    applyNow();
    
    // Повторюємо кілька разів для гарантії
    setTimeout(forceUltraCompact, 100);
    setTimeout(forceUltraCompact, 500);
    setTimeout(forceUltraCompact, 1000);
    
    // При зміні розміру вікна
    window.addEventListener('resize', () => {
        setTimeout(forceUltraCompact, 50);
    });
    
    // Спостерігач за DOM змінами
    if ('MutationObserver' in window) {
        const observer = new MutationObserver(() => {
            setTimeout(forceUltraCompact, 50);
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'style']
        });
    }
    
})();
