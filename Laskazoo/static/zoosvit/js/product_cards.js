/* static/zoosvit/js/product_cards.js - ВИПРАВЛЕНА ВЕРСІЯ */
(function (w, d) {
  'use strict';

  // ===== Налаштування
  const EXTRA_BUFFER = 30;
  const MEASURE_CLASS = 'is-measuring';
  const NS = 'ProductCards';
  const BATCH_SIZE = 5;
  const BATCH_DELAY = 8;

  // ===== Кеш системи
  const heightCache = new Map();
  const cardMeasured = new WeakMap();
  let isPreloading = false;
  let preloadComplete = false;

  // ===== Допоміжні функції
  const readLimits = (() => {
    let cachedLimits = null;
    return () => {
      if (!cachedLimits) {
        const CSS = getComputedStyle(d.documentElement);
        const MIN = parseInt(CSS.getPropertyValue('--prod-min-height')) || 320;
        const MAX = parseInt(CSS.getPropertyValue('--prod-max-height')) || 820;
        cachedLimits = { MIN, MAX };
      }
      return cachedLimits;
    };
  })();

  const clampH = (v, MIN, MAX) => Math.min(MAX, Math.max(MIN, Math.max(0, v)));

  const getCardId = (card) => {
    if (!card.dataset.cardId) {
      card.dataset.cardId = 'card_' + Math.random().toString(36).substr(2, 9);
    }
    return card.dataset.cardId;
  };

  // Ін'єкція стилю (тільки один раз)
  const injectMeasureCSS = (() => {
    let injected = false;
    return () => {
      if (injected) return;
      const style = d.createElement('style');
      style.id = 'measure-style';
      style.textContent = `
        .prod-card.${MEASURE_CLASS} .card-back {
          position: static !important;
          inset: auto !important;
          height: auto !important;
          max-height: none !important;
          visibility: hidden !important;
          pointer-events: none !important;
          opacity: 1 !important;
        }`;
      d.head.appendChild(style);
      injected = true;
    };
  })();

  // ===== ВИПРАВЛЕНА ФУНКЦІЯ ВИМІРУ - синхронна з одразу застосуванням
  function measureCardOptimized(card) {
    if (!card) return 0;

    const cardId = getCardId(card);

    // Якщо вже вимірювали - повертаємо з кешу
    if (cardMeasured.has(card)) {
      const h = heightCache.get(cardId);
      if (h) {
        card.style.setProperty('--hover-height', h + 'px');
        return h;
      }
    }

    // Перевірка data-атрибуту
    const ds = parseInt(card.dataset.hoverH || '0');
    const { MIN, MAX } = readLimits();
    if (ds) {
      const h = clampH(ds, MIN, MAX);
      heightCache.set(cardId, h);
      cardMeasured.set(card, true);
      card.style.setProperty('--hover-height', h + 'px');
      return h;
    }

    const back = card.querySelector('.card-back');
    if (!back) return 0;

    // Оптимізація зображень
    const images = back.querySelectorAll('img');
    for (let i = 0; i < images.length; i++) {
      const img = images[i];
      const hasSize = img.getAttribute('width') || img.getAttribute('height') ||
                      img.style.width || img.style.height || img.style.aspectRatio;
      if (!hasSize) {
        img.style.cssText += 'aspect-ratio:4/5;width:100%;height:auto;';
      }
      img.removeAttribute?.('srcset');
    }

    // ✅ СИНХРОННИЙ ВИМІР БЕЗ ЗАТРИМОК
    card.classList.add(MEASURE_CLASS);
    
    let desired = back.scrollHeight;
    const last = back.lastElementChild;
    if (last) {
      desired += parseFloat(getComputedStyle(last).marginBottom) || 0;
    }
    desired = Math.ceil(desired + EXTRA_BUFFER);

    card.classList.remove(MEASURE_CLASS);

    const h = clampH(desired, MIN, MAX);

    // Дебаг
    if (w.__CARD_DEBUG) {
      console.log(`[MEASURE] Card ${cardId}: desired=${desired}, clamped=${h}`);
      if (h < desired) card.dataset.clamped = '1';
      else card.removeAttribute('data-clamped');
    }

    // Зберігаємо в кеш та DOM
    heightCache.set(cardId, h);
    cardMeasured.set(card, true);
    card.dataset.hoverH = String(h);
    
    // ✅ ЗАСТОСОВУЄМО CSS ЗМІННУ ОДРАЗУ
    card.style.setProperty('--hover-height', h + 'px');

    return h;
  }

  // ===== ПОКРАЩЕНИЙ ПРЕДВАРИТЕЛЬНИЙ РОЗРАХУНОК
  function preloadAllCardsOptimized() {
    if (isPreloading || preloadComplete) return;
    
    console.log('[PRELOAD] Starting optimized preload...');
    isPreloading = true;

    const allCards = Array.from(d.querySelectorAll('.prod-card'));
    let processed = 0;
    
    // Фільтруємо вже оброблені картки
    const cardsToProcess = allCards.filter(card => !cardMeasured.has(card));
    
    if (cardsToProcess.length === 0) {
      isPreloading = false;
      preloadComplete = true;
      console.log('[PRELOAD] All cards already processed');
      return;
    }
    
    function processNextBatch() {
      const batch = cardsToProcess.slice(processed, processed + BATCH_SIZE);
      
      if (batch.length === 0) {
        isPreloading = false;
        preloadComplete = true;
        console.log(`[PRELOAD] Complete! Processed ${processed}/${cardsToProcess.length} new cards`);
        
        // Виклик користувацького callback
        if (typeof w.onCardPreloadComplete === 'function') {
          w.onCardPreloadComplete();
        }
        return;
      }
      
      // ✅ Синхронна batch обробка - без RAF
      batch.forEach(card => {
        measureCardOptimized(card);
        processed++;
      });
      
      setTimeout(processNextBatch, BATCH_DELAY);
    }
    
    // Починаємо обробку одразу після DOM готовності
    if (d.readyState === 'loading') {
      d.addEventListener('DOMContentLoaded', () => {
        setTimeout(processNextBatch, 50);
      });
    } else {
      setTimeout(processNextBatch, 50);
    }
  }

  // ===== МИТТЄВЕ ЗАСТОСУВАННЯ З КЕШУ
  function applyFromCacheOptimized(card) {
    const cardId = getCardId(card);
    
    if (heightCache.has(cardId)) {
      const h = heightCache.get(cardId);
      card.style.setProperty('--hover-height', h + 'px');
      return true;
    }
    
    // Якщо в кеші немає - спробувати з data-атрибуту
    const stored = parseInt(card.dataset.hoverH || '0');
    if (stored) {
      const { MIN, MAX } = readLimits();
      const h = clampH(stored, MIN, MAX);
      heightCache.set(cardId, h);
      cardMeasured.set(card, true);
      card.style.setProperty('--hover-height', h + 'px');
      return true;
    }
    
    // Виміряти зараз
    measureCardOptimized(card);
    return true;
  }

  // ===== ОПТИМІЗОВАНІ ПІГУЛКИ ВАРІАНТІВ
  function initVariantPillsOptimized(ctx = d) {
    const cards = ctx.querySelectorAll('.prod-card');
    
    for (let i = 0; i < cards.length; i++) {
      const card = cards[i];
      const pills = card.querySelectorAll('.variant-pill');
      if (!pills.length) continue;

      // Кешуємо всі елементи одразу
      const elements = {
        imgF: card.querySelector('.card-front img'),
        priceF: card.querySelector('.card-front .card-price'),
        skuF: card.querySelector('.card-front .card-article'),
        titleF: card.querySelector('.card-front .card-title'),
        imgB: card.querySelector('.card-back img'),
        priceB: card.querySelector('.card-back .card-price'),
        skuB: card.querySelector('.card-back .card-article'),
        titleB: card.querySelector('.card-back .card-title'),
        addBtn: card.querySelector('.card-actions .add-to-cart'),
        favBtn: card.querySelector('.card-actions .js-fav')
      };

      const addBase = elements.addBtn ? (elements.addBtn.dataset.addBase || elements.addBtn.href.split('?')[0]) : '';
      const baseTitle = (elements.titleF?.dataset.baseTitle || elements.titleF?.textContent || '').trim();

      const setText = (el, t) => { if (el) el.textContent = t; };
      const setSrc = (el, src) => { if (el) { el.removeAttribute('srcset'); el.src = src; } };
      
      const suffix = (p) => {
        const w = p.dataset.weight;
        const s = p.dataset.size;
        if (w && !isNaN(Number(w))) return ` — ${Number(w)} кг`;
        if (s) return ` — ${s}`;
        return '';
      };

      function applyVariant(pill) {
        // Оновлюємо активний стан
        for (let j = 0; j < pills.length; j++) {
          pills[j].classList.remove('active');
        }
        pill.classList.add('active');

        const img = pill.dataset.image;
        const sku = pill.dataset.sku || '—';
        const price = pill.dataset.price;
        const vid = pill.dataset.vid;

        // Batch DOM updates
        if (img) {
          setSrc(elements.imgF, img);
          setSrc(elements.imgB, img);
        }

        setText(elements.skuF, `Артикул: ${sku}`);
        setText(elements.skuB, `Артикул: ${sku}`);
        
        if (price) {
          setText(elements.priceF, `₴ ${price}`);
          setText(elements.priceB, `₴ ${price}`);
        }

        const newTitle = baseTitle + suffix(pill);
        setText(elements.titleF, newTitle);
        setText(elements.titleB, newTitle);

        if (elements.addBtn && addBase) {
          elements.addBtn.href = `${addBase}?variant=${vid}`;
        }

        if (elements.favBtn) {
          elements.favBtn.dataset.variant = vid;
          const isOn = !!(w.__favVarSet && w.__favVarSet.has(Number(vid)));
          elements.favBtn.classList.toggle('is-on', isOn);
          elements.favBtn.setAttribute('aria-pressed', isOn ? 'true' : 'false');
        }

        // Перевимірити після зміни варіанта
        api.recomputeOneCard(card);
      }

      // Додаємо event listeners
      for (let j = 0; j < pills.length; j++) {
        pills[j].addEventListener('click', (e) => {
          e.preventDefault(); 
          e.stopPropagation(); 
          applyVariant(pills[j]);
        });
      }

      // Застосовуємо перший варіант
      if (pills[0]) applyVariant(pills[0]);
    }
  }

  // ===== ОПТИМІЗАЦІЯ ЗАВАНТАЖЕННЯ ЗОБРАЖЕНЬ
  function optimizeImagesOptimized() {
    let imageLoadTimeout;
    
    d.addEventListener('load', (e) => {
      const img = e.target;
      if (!(img instanceof HTMLImageElement)) return;
      
      const card = img.closest('.prod-card');
      if (!card) return;

      // Debounce для множинних зображень
      clearTimeout(imageLoadTimeout);
      imageLoadTimeout = setTimeout(() => {
        // Перевимірюємо тільки якщо картка ще не оброблена
        if (!cardMeasured.has(card)) {
          api.recomputeOneCard(card);
        }
      }, 100);
    }, true);
  }

  // ===== ПОКРАЩЕНЕ ПУБЛІЧНЕ API
  const api = {
    init(ctx) { 
      console.log('[INIT] ProductCards optimized version started');
      
      // Ін'єкція CSS
      injectMeasureCSS();
      
      // Ініціалізація компонентів
      initVariantPillsOptimized(ctx || d);
      optimizeImagesOptimized();
      
      // Запускаємо предварительний розрахунок
      preloadAllCardsOptimized();
    },
    
    measureAll() {
      console.log('[API] Manual measureAll - using optimized preload');
      preloadAllCardsOptimized();
    },
    
    recomputeOneCard(card) {
      if (!card) return;
      
      const cardId = getCardId(card);
      
      // Очищаємо кеш для цієї картки
      heightCache.delete(cardId);
      cardMeasured.delete(card);
      delete card.dataset.hoverH;
      
      // Перевимірюємо синхронно
      measureCardOptimized(card);
    },

    clearCache() {
      console.log('[CLEAR CACHE] Clearing all cache');
      heightCache.clear();
      preloadComplete = false;
      isPreloading = false;
      
      d.querySelectorAll('.prod-card').forEach(card => {
        cardMeasured.delete(card);
        delete card.dataset.hoverH;
        delete card.dataset.cardId;
        card.style.removeProperty('--hover-height');
      });
    },

    getStats() {
      return {
        cacheSize: heightCache.size,
        preloadComplete,
        isPreloading,
        totalCards: d.querySelectorAll('.prod-card').length
      };
    },

    applyInstant(card) {
      return applyFromCacheOptimized(card);
    },

    forceCompletePreload() {
      if (isPreloading) {
        console.log('[FORCE] Completing preload...');
        isPreloading = false;
        preloadComplete = true;
      }
    },

    getCardInfo(card) {
      if (!card) return null;
      const cardId = getCardId(card);
      return {
        id: cardId,
        cached: heightCache.has(cardId),
        height: heightCache.get(cardId),
        measured: cardMeasured.has(card)
      };
    }
  };

  // Експортуємо у window
  w[NS] = api;

  // ===== ОПТИМІЗОВАНА ІНІЦІАЛІЗАЦІЯ
  const boot = () => {
    console.log('[BOOT] ProductCards optimized version...');
    api.init();
  };

  if (d.readyState === 'loading') {
    d.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  // При завантаженні window - переконуємося що preload завершений
  w.addEventListener('load', () => {
    console.log('[LOAD] Window loaded, ensuring all cards measured');
    // ✅ Перевіряємо ВСІ картки і застосовуємо вимірювання
    d.querySelectorAll('.prod-card').forEach(card => {
      if (!cardMeasured.has(card)) {
        measureCardOptimized(card);
      }
    });
  }, { once: true });

  // Автоматичне застосування для нових карток (MutationObserver)
  if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'childList') {
          const newCards = [];
          for (const node of mutation.addedNodes) {
            if (node.nodeType === 1) {
              if (node.classList?.contains('prod-card')) {
                newCards.push(node);
              } else {
                newCards.push(...node.querySelectorAll?.('.prod-card') || []);
              }
            }
          }
          
          if (newCards.length > 0) {
            console.log(`[OBSERVER] Found ${newCards.length} new cards`);
            newCards.forEach(card => {
              initVariantPillsOptimized(card.parentElement);
              measureCardOptimized(card);
            });
          }
        }
      }
    });

    observer.observe(d.body, {
      childList: true,
      subtree: true
    });
  }

  // Дебаг
  if (w.__CARD_DEBUG) {
    w.__cardDebug = api;
    console.log('Debug mode enabled. Use __cardDebug for debugging.');
  }

})(window, document);
