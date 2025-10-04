// optimized-dynamic-spacing.js - оптимізований розрахунок висоти з кешуванням
(function() {
    'use strict';

    // ===== КЕШ ТА ОПТИМІЗАЦІЯ =====
    let spacingCache = new Map();
    let lastWindowWidth = 0;
    let lastCalculationTime = 0;
    let isCalculating = false;
    
    const CACHE_DURATION = 5000; // 5 секунд
    const CALCULATION_THROTTLE = 150; // мс
    
    // Дебаг лічильник
    let calculationCount = 0;

    // ===== УТИЛІТАРНІ ФУНКЦІЇ =====
    
    function generateCacheKey(grid) {
        const cards = grid.querySelectorAll('.prod-card, .subcategory-card, .category-card');
        const cardCount = cards.length;
        const windowWidth = window.innerWidth;
        const gridType = grid.className;
        const pathname = window.location.pathname;
        
        return `${pathname}:${gridType}:${cardCount}:${windowWidth}`;
    }
    
    function isValidCache(cacheKey) {
        const cached = spacingCache.get(cacheKey);
        if (!cached) return false;
        
        const now = Date.now();
        return (now - cached.timestamp) < CACHE_DURATION;
    }
    
    function shouldRecalculate() {
        const now = Date.now();
        const currentWidth = window.innerWidth;
        
        // Перевіряємо чи змінилась ширина екрану значно
        const widthChanged = Math.abs(currentWidth - lastWindowWidth) > 50;
        
        // Перевіряємо throttling
        const timeElapsed = now - lastCalculationTime;
        const throttleOk = timeElapsed > CALCULATION_THROTTLE;
        
        return !isCalculating && throttleOk && (widthChanged || timeElapsed > CACHE_DURATION);
    }

    // ===== ОСНОВНА ФУНКЦІЯ РОЗРАХУНКУ =====
    
    function calculateDynamicSpacing() {
        if (!shouldRecalculate()) {
            console.log('[SPACING] Skipping calculation (cache/throttle)');
            return Promise.resolve();
        }

        isCalculating = true;
        calculationCount++;
        const startTime = performance.now();
        
        console.log(`[SPACING] Starting calculation #${calculationCount}`);

        return new Promise((resolve) => {
            requestAnimationFrame(() => {
                try {
                    performCalculation();
                    
                    const endTime = performance.now();
                    console.log(`[SPACING] Calculation #${calculationCount} completed in ${(endTime - startTime).toFixed(2)}ms`);
                    
                    lastCalculationTime = Date.now();
                    lastWindowWidth = window.innerWidth;
                    
                } catch (error) {
                    console.error('[SPACING] Calculation error:', error);
                } finally {
                    isCalculating = false;
                    resolve();
                }
            });
        });
    }
    
    function performCalculation() {
        // Знаходимо всі сітки з картками
        const grids = document.querySelectorAll('.product-grid, .subcategory-grid, .main-category-grid');
        
        grids.forEach(grid => {
            const cacheKey = generateCacheKey(grid);
            
            // Перевіряємо кеш
            if (isValidCache(cacheKey)) {
                const cached = spacingCache.get(cacheKey);
                applySpacingFromCache(grid, cached.data);
                console.log(`[SPACING] Cache hit for grid: ${cacheKey}`);
                return;
            }
            
            // Виконуємо розрахунок
            const spacingData = calculateGridSpacing(grid);
            
            // Зберігаємо в кеш
            spacingCache.set(cacheKey, {
                timestamp: Date.now(),
                data: spacingData
            });
            
            // Застосовуємо результати
            applySpacing(grid, spacingData);
            
            console.log(`[SPACING] New calculation for grid: ${cacheKey}`, spacingData);
        });
        
        // Застосовуємо глобальні оптимізації
        applyGlobalOptimizations();
        
        // Очищуємо старий кеш
        cleanupCache();
    }
    
    function calculateGridSpacing(grid) {
        const cards = grid.querySelectorAll('.prod-card, .subcategory-card, .category-card');
        const cardCount = cards.length;
        
        if (cardCount === 0) {
            return { cardCount: 0, rowClass: 'empty-grid', minHeight: 200 };
        }
        
        // Отримуємо кількість колонок в сітці з кешуванням
        const gridColumns = getGridColumns(grid);
        const rows = Math.ceil(cardCount / gridColumns);
        
        // Визначаємо клас та мінімальну висоту
        let rowClass, minHeight, marginBottom;
        
        if (cardCount <= 4) {
            rowClass = 'cards-1-row';
            minHeight = 280;
            marginBottom = 10;
        } else if (cardCount <= 8) {
            rowClass = 'cards-2-rows';
            minHeight = 350;
            marginBottom = 15;
        } else if (cardCount <= 12) {
            rowClass = 'cards-3-rows';
            minHeight = 420;
            marginBottom = 20;
        } else if (cardCount <= 20) {
            rowClass = 'cards-4-5-rows';
            minHeight = 520;
            marginBottom = 25;
        } else {
            rowClass = 'cards-many-rows';
            minHeight = 'auto';
            marginBottom = 30;
        }
        
        return { 
            cardCount, 
            rowClass, 
            minHeight, 
            marginBottom, 
            gridColumns, 
            rows 
        };
    }
    
    // Кешований розрахунок кількості колонок
    let gridColumnsCache = new WeakMap();
    
    function getGridColumns(grid) {
        if (gridColumnsCache.has(grid)) {
            return gridColumnsCache.get(grid);
        }
        
        const computedStyle = window.getComputedStyle(grid);
        const gridTemplateColumns = computedStyle.gridTemplateColumns;
        
        let gridColumns;
        if (gridTemplateColumns === 'none') {
            // Припускаємо стандартну сітку залежно від розміру екрану
            gridColumns = window.innerWidth >= 1200 ? 4 : window.innerWidth >= 768 ? 3 : 2;
        } else {
            gridColumns = gridTemplateColumns.split(' ').length;
        }
        
        gridColumnsCache.set(grid, gridColumns);
        return gridColumns;
    }
    
    function applySpacing(grid, spacingData) {
        // Прибираємо всі попередні класи
        grid.classList.remove('cards-1-row', 'cards-2-rows', 'cards-3-rows', 'cards-4-5-rows', 'cards-many-rows', 'empty-grid');
        
        // Додаємо новий клас
        grid.classList.add(spacingData.rowClass);
        
        // Встановлюємо атрибут з кількістю карток для CSS
        grid.setAttribute('data-card-count', spacingData.cardCount);
        
        // Застосовуємо стилі через CSS кастомні властивості
        if (spacingData.minHeight !== 'auto') {
            grid.style.setProperty('--dynamic-min-height', spacingData.minHeight + 'px');
        } else {
            grid.style.removeProperty('--dynamic-min-height');
        }
        
        grid.style.setProperty('--dynamic-margin-bottom', spacingData.marginBottom + 'px');
    }
    
    function applySpacingFromCache(grid, spacingData) {
        applySpacing(grid, spacingData);
    }
    
    function applyGlobalOptimizations() {
        // Застосовуємо оптимізації тільки якщо вони ще не застосовані
        if (document.body.hasAttribute('data-spacing-optimized')) {
            return;
        }
        
        const path = window.location.pathname;
        const isMainCatalog = path === '/categories/';
        const isCategoryPage = path.includes('/categories/') && path !== '/categories/';
        
        // Додаємо класи до body
        document.body.classList.toggle('catalog-page', isMainCatalog);
        document.body.classList.toggle('category-page', isCategoryPage);
        
        if (isMainCatalog || isCategoryPage) {
            // Оптимізуємо відступи для елементів сторінки
            const optimizations = [
                { selector: '.catalog-page-heading', styles: { marginBottom: '10px' } },
                { selector: '.top-cats-bar', styles: { marginBottom: '8px' } },
                { selector: '.breadcrumbs', styles: { marginBottom: '8px', paddingBottom: '3px' } },
                { selector: '.catalog-controls', styles: { marginBottom: '10px' } },
                { selector: '.catalog-header', styles: { marginBottom: '10px' } },
                { selector: '.category-nav', styles: { marginBottom: '10px' } },
                { selector: '.pagination-wrapper', styles: { marginTop: '10px', marginBottom: '10px' } },
                { selector: 'footer', styles: { marginTop: '15px' } }
            ];
            
            optimizations.forEach(({ selector, styles }) => {
                const element = document.querySelector(selector);
                if (element && !element.hasAttribute('data-optimized')) {
                    Object.assign(element.style, styles);
                    element.setAttribute('data-optimized', 'true');
                }
            });
            
            // Спеціальна обробка для пустих сторінок
            const emptyMessages = document.querySelectorAll('.no-favourites, .no-products');
            emptyMessages.forEach(msg => {
                if (msg.hasAttribute('data-optimized')) return;
                
                const container = msg.closest('.product-grid, .subcategory-grid, .main-category-grid') || msg.parentElement;
                if (container) {
                    container.style.minHeight = '200px';
                    container.style.marginBottom = '20px';
                    msg.setAttribute('data-optimized', 'true');
                }
            });
        }
        
        document.body.setAttribute('data-spacing-optimized', 'true');
    }
    
    function cleanupCache() {
        const now = Date.now();
        const maxAge = CACHE_DURATION * 2; // Подвійний термін життя для очищення
        
        for (const [key, value] of spacingCache.entries()) {
            if (now - value.timestamp > maxAge) {
                spacingCache.delete(key);
            }
        }
        
        // Очищуємо кеш колонок при зміні розміру екрану
        if (Math.abs(window.innerWidth - lastWindowWidth) > 100) {
            gridColumnsCache = new WeakMap();
        }
    }

    // ===== ОБРОБНИКИ ПОДІЙ =====
    
    let resizeTimeout;
    function handleResize() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            console.log('[SPACING] Resize triggered recalculation');
            calculateDynamicSpacing();
        }, CALCULATION_THROTTLE);
    }
    
    // Оптимізований MutationObserver
    let mutationObserver;
    function initMutationObserver() {
        if (!('MutationObserver' in window) || mutationObserver) return;
        
        mutationObserver = new MutationObserver(function(mutations) {
            let shouldRecalc = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    // Перевіряємо, чи додались/видалились картки
                    const hasCardChanges = Array.from(mutation.addedNodes).some(node => 
                        node.nodeType === 1 && node.classList && (
                            node.classList.contains('prod-card') || 
                            node.classList.contains('subcategory-card') || 
                            node.classList.contains('category-card')
                        )
                    );
                    
                    const hasCardRemovals = Array.from(mutation.removedNodes).some(node => 
                        node.nodeType === 1 && node.classList && (
                            node.classList.contains('prod-card') || 
                            node.classList.contains('subcategory-card') || 
                            node.classList.contains('category-card')
                        )
                    );
                    
                    if (hasCardChanges || hasCardRemovals) {
                        shouldRecalc = true;
                    }
                }
            });
            
            if (shouldRecalc) {
                console.log('[SPACING] DOM mutation triggered recalculation');
                setTimeout(calculateDynamicSpacing, 100);
            }
        });
        
        // Спостерігаємо за змінами в сітках
        const grids = document.querySelectorAll('.product-grid, .subcategory-grid, .main-category-grid');
        grids.forEach(grid => {
            mutationObserver.observe(grid, { childList: true, subtree: true });
        });
    }

    // ===== ПУБЛІЧНЕ API =====
    
    const api = {
        calculate: calculateDynamicSpacing,
        clearCache: () => {
            spacingCache.clear();
            gridColumnsCache = new WeakMap();
            document.body.removeAttribute('data-spacing-optimized');
            console.log('[SPACING] Cache cleared');
        },
        getStats: () => ({
            cacheSize: spacingCache.size,
            calculationCount,
            isCalculating,
            lastCalculationTime
        })
    };
    
    // Експортуємо в глобальний об'єкт
    window.DynamicSpacing = api;
    window.recalculateSpacing = calculateDynamicSpacing; // Зворотна сумісність

    // ===== ІНІЦІАЛІЗАЦІЯ =====
    
    function init() {
        console.log('[SPACING] Initializing optimized dynamic spacing');
        
        // Початковий розрахунок
        calculateDynamicSpacing();
        
        // Ініціалізуємо спостерігачів
        initMutationObserver();
        
        // Обробники подій
        window.addEventListener('resize', handleResize);
        
        console.log('[SPACING] Initialization complete');
    }

    // Запускаємо при завантаженні DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Запускаємо при завантаженні всієї сторінки
    window.addEventListener('load', () => {
        console.log('[SPACING] Window loaded, recalculating');
        calculateDynamicSpacing();
    });

    // Дебаг консольні команди
    if (window.__CARD_DEBUG) {
        window.__spacingDebug = api;
        console.log('Spacing debug mode enabled. Use __spacingDebug for debugging.');
    }

})();