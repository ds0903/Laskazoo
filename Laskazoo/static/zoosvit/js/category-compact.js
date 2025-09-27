// category-compact.js - специфічно для сторінок категорій
(function() {
    'use strict';
    
    function forceCompactLayout() {
        // Перевіряємо чи це не головна сторінка
        if (document.body.classList.contains('home-page')) {
            return;
        }
        
        // Додаємо клас ultra-compact до body
        document.body.classList.add('ultra-compact');
        
        // Агресивно прибираємо відступи з ключових елементів
        const elementsToFix = [
            { selector: '.site-main', styles: { minHeight: 'auto', paddingBottom: '0', marginBottom: '0' } },
            { selector: '.product-grid', styles: { marginBottom: '2px', paddingBottom: '0', minHeight: 'auto' } },
            { selector: '.pagination-wrapper', styles: { marginTop: '2px', marginBottom: '2px', padding: '0' } },
            { selector: '.catalog.container', styles: { paddingBottom: '0', marginBottom: '0', minHeight: 'auto' } },
            { selector: '.catalog-wrapper', styles: { paddingBottom: '0', marginBottom: '0', minHeight: 'auto' } },
            { selector: '.catalog-main', styles: { paddingBottom: '0', marginBottom: '0', minHeight: 'auto' } },
            { selector: 'footer', styles: { marginTop: '3px', paddingTop: '10px' } },
            { selector: '.site-content', styles: { paddingBottom: '0', marginBottom: '0' } },
        ];
        
        elementsToFix.forEach(({ selector, styles }) => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                Object.assign(element.style, styles);
            });
        });
        
        // Прибираємо відступи з усіх section і container в main
        const sections = document.querySelectorAll('.site-main section, .site-main .container');
        sections.forEach(section => {
            section.style.marginBottom = '0';
            section.style.paddingBottom = '0';
        });
        
        // Останній елемент в main
        const lastElement = document.querySelector('.site-main > *:last-child');
        if (lastElement) {
            lastElement.style.marginBottom = '0';
            lastElement.style.paddingBottom = '0';
        }
        
        // Спеціально для пагінації - розміщуємо максимально близько до карток
        const productGrid = document.querySelector('.product-grid');
        const paginationWrapper = document.querySelector('.pagination-wrapper');
        
        if (productGrid && paginationWrapper) {
            productGrid.style.marginBottom = '1px';
            paginationWrapper.style.marginTop = '1px';
            paginationWrapper.style.marginBottom = '1px';
        }
        
        console.log('Compact layout applied');
    }
    
    // Функція для постійного моніторингу та застосування стилів
    function startMonitoring() {
        // Застосовуємо одразу
        forceCompactLayout();
        
        // Повторюємо через інтервали
        const intervals = [50, 100, 200, 500, 1000, 2000];
        intervals.forEach(delay => {
            setTimeout(forceCompactLayout, delay);
        });
        
        // Моніторинг змін DOM
        if ('MutationObserver' in window) {
            const observer = new MutationObserver(() => {
                setTimeout(forceCompactLayout, 50);
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class']
            });
        }
        
        // При зміні розміру вікна
        window.addEventListener('resize', () => {
            setTimeout(forceCompactLayout, 100);
        });
    }
    
    // Запускаємо миттєво
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startMonitoring);
    } else {
        startMonitoring();
    }
    
    // Також при повному завантаженні
    window.addEventListener('load', forceCompactLayout);
    
})();
