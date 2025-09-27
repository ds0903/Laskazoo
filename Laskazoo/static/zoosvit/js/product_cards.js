/* static/zoosvit/js/product_cards.js - ВЕРСІЯ З ПРЕДВАРИТЕЛЬНИМ РОЗРАХУНКОМ */
(function (w, d) {
  'use strict';

  // ===== Налаштування
  const EXTRA_BUFFER = 30;
  const MEASURE_CLASS = 'is-measuring';
  const NS = 'ProductCards';

  // ===== Кеш системи
  const heightCache = new Map();
  const cardObserver = new WeakMap();
  const preloadQueue = [];
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

  // Ін'єкція стилю
  (function injectMeasureCSS() {
    if (d.getElementById('measure-style')) return;
    const style = d.createElement('style');
    style.id = 'measure-style';
    style.textContent =
      `.prod-card.${MEASURE_CLASS} .card-back{
         position: static !important;
         inset: auto !important;
         height: auto !important;
         max-height: none !important;
         visibility: hidden !important;
         pointer-events: none !important;
         opacity: 1 !important;
       }`;
    d.head.appendChild(style);
  })();

  // ===== ОСНОВНА ФУНКЦІЯ ВИМІРУ
  function measureCardSync(card) {
    if (!card) return 0;

    const cardId = getCardId(card);

    // Перевірка кешу
    if (heightCache.has(cardId)) {
      const h = heightCache.get(cardId);
      card.style.setProperty('--hover-height', h + 'px');
      return h;
    }

    // Перевірка data-атрибуту
    const ds = parseInt(card.dataset.hoverH || '0');
    const { MIN, MAX } = readLimits();
    if (ds) {
      const h = clampH(ds, MIN, MAX);
      heightCache.set(cardId, h);
      card.style.setProperty('--hover-height', h + 'px');
      return h;
    }

    const back = card.querySelector('.card-back');
    if (!back) return 0;

    // Оптимізація зображень
    back.querySelectorAll('img').forEach(img => {
      const hasSize = img.getAttribute('width') || img.getAttribute('height') ||
                      img.style.width || img.style.height || img.style.aspectRatio;
      if (!hasSize) {
        img.style.aspectRatio = '4 / 5';
        img.style.width = '100%';
        img.style.height = 'auto';
      }
      img.removeAttribute?.('srcset');
    });

    // Вимір
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
      if (h < desired) card.dataset.clamped = '1';
      else card.removeAttribute('data-clamped');
    }

    // Зберігаємо в кеш
    heightCache.set(cardId, h);
    card.dataset.hoverH = String(h);
    card.style.setProperty('--hover-height', h + 'px');
    cardObserver.set(card, true);

    console.log(`[PRELOAD] Card ${cardId}: ${h}px`);
    return h;
  }

  // ===== ПРЕДВАРИТЕЛЬНИЙ РОЗРАХУНОК ВСІХ КАРТОК
  function preloadAllCards() {
    if (isPreloading || preloadComplete) return;
    
    console.log('[PRELOAD] Starting preload of all cards...');
    isPreloading = true;

    const allCards = Array.from(d.querySelectorAll('.prod-card'));
    let processed = 0;
    
    function processNextBatch() {
      const batchSize = 3; // По 3 картки за раз
      const batch = allCards.slice(processed, processed + batchSize);
      
      if (batch.length === 0) {
        // Всі картки оброблені
        isPreloading = false;
        preloadComplete = true;
        console.log(`[PRELOAD] Complete! Processed ${processed} cards`);
        return;
      }
      
      // Обробляємо поточну партію
      batch.forEach(card => {
        if (!cardObserver.has(card)) {
          measureCardSync(card);
        }
        processed++;
      });
      
      console.log(`[PRELOAD] Progress: ${processed}/${allCards.length} cards`);
      
      // Плануємо наступну партію з невеликою затримкою
      setTimeout(processNextBatch, 10);
    }
    
    // Починаємо обробку після завантаження DOM
    if (d.readyState === 'loading') {
      d.addEventListener('DOMContentLoaded', () => {
        setTimeout(processNextBatch, 100);
      });
    } else {
      setTimeout(processNextBatch, 100);
    }
  }

  // ===== ШВИДКЕ ЗАСТОСУВАННЯ З КЕШУ
  function applyFromCache(card) {
    const cardId = getCardId(card);
    
    if (heightCache.has(cardId)) {
      const h = heightCache.get(cardId);
      card.style.setProperty('--hover-height', h + 'px');
      console.log(`[INSTANT] Card ${cardId}: ${h}px from cache`);
      return true;
    }
    
    // Якщо в кеші немає - виміряти зараз
    measureCardSync(card);
    return true;
  }

  // ===== Пігулки варіантів
  function initVariantPills(ctx = d) {
    ctx.querySelectorAll('.prod-card').forEach(card => {
      const pills = card.querySelectorAll('.variant-pill');
      if (!pills.length) return;

      const imgF   = card.querySelector('.card-front img');
      const priceF = card.querySelector('.card-front .card-price');
      const skuF   = card.querySelector('.card-front .card-article');
      const titleF = card.querySelector('.card-front .card-title');

      const imgB   = card.querySelector('.card-back img');
      const priceB = card.querySelector('.card-back .card-price');
      const skuB   = card.querySelector('.card-back .card-article');
      const titleB = card.querySelector('.card-back .card-title');

      const addBtn  = card.querySelector('.card-actions .add-to-cart');
      const favBtn  = card.querySelector('.card-actions .js-fav');
      const addBase = addBtn ? (addBtn.dataset.addBase || addBtn.href.split('?')[0]) : '';

      const baseTitle = (titleF?.dataset.baseTitle || titleF?.textContent || '').trim();

      const setText = (el, t) => { if (el) el.textContent = t; };
      const suffix = (p) => {
        const w = p.dataset.weight; const s = p.dataset.size;
        if (w && !isNaN(Number(w))) return ` — ${Number(w)} кг`;
        if (s) return ` — ${s}`;
        return '';
      };

      function apply(pill) {
        pills.forEach(b => b.classList.remove('active'));
        pill.classList.add('active');

        const img   = pill.dataset.image;
        const sku   = pill.dataset.sku || '—';
        const price = pill.dataset.price;
        const vid   = pill.dataset.vid;

        if (img) {
          if (imgF) { imgF.removeAttribute('srcset'); imgF.src = img; }
          if (imgB) { imgB.removeAttribute('srcset'); imgB.src = img; }
        }

        setText(skuF, `Артикул: ${sku}`);
        setText(skuB, `Артикул: ${sku}`);
        if (price) { setText(priceF, `₴ ${price}`); setText(priceB, `₴ ${price}`); }

        if (titleF) titleF.textContent = baseTitle + suffix(pill);
        if (titleB) titleB.textContent = baseTitle + suffix(pill);

        if (addBtn && addBase) addBtn.href = `${addBase}?variant=${vid}`;

        if (favBtn) {
          favBtn.dataset.variant = vid;
          const isOn = !!(w.__favVarSet && w.__favVarSet.has(Number(vid)));
          favBtn.classList.toggle('is-on', isOn);
          favBtn.setAttribute('aria-pressed', isOn ? 'true' : 'false');
        }

        // Перевимірити після зміни варіанта
        api.recomputeOneCard(card);
      }

      pills.forEach(p => p.addEventListener('click', e => {
        e.preventDefault(); 
        e.stopPropagation(); 
        apply(p);
      }));

      apply(pills[0]);
    });
  }

  // ===== ОПТИМІЗАЦІЯ ЗАВАНТАЖЕННЯ ЗОБРАЖЕНЬ
  function optimizeImages() {
    d.addEventListener('load', (e) => {
      const img = e.target;
      if (!(img instanceof HTMLImageElement)) return;
      
      const card = img.closest('.prod-card');
      if (!card) return;

      // Якщо preload ще не завершений - перевимірити
      if (!preloadComplete) {
        setTimeout(() => {
          api.recomputeOneCard(card);
        }, 50);
      }
    }, true);
  }

  // ===== Публічне API
  const api = {
    init(ctx) { 
      console.log('[INIT] ProductCards with preloading started');
      initVariantPills(ctx || d);
      optimizeImages();
      
      // Запускаємо предварительний розрахунок
      preloadAllCards();
    },
    
    measureAll() {
      console.log('[API] Manual measureAll - using preload');
      preloadAllCards();
    },
    
    recomputeOneCard(card) {
      if (!card) return;
      
      const cardId = getCardId(card);
      console.log(`[RECOMPUTE] Card ${cardId}`);
      
      // Очищаємо кеш для цієї картки
      heightCache.delete(cardId);
      cardObserver.delete(card);
      delete card.dataset.hoverH;
      
      // Перевимірюємо
      requestAnimationFrame(() => measureCardSync(card));
    },

    clearCache() {
      console.log('[CLEAR CACHE] Clearing all cache');
      heightCache.clear();
      preloadComplete = false;
      d.querySelectorAll('.prod-card').forEach(card => {
        cardObserver.delete(card);
        delete card.dataset.hoverH;
        delete card.dataset.cardId;
      });
    },

    getStats() {
      return {
        cacheSize: heightCache.size,
        preloadComplete,
        isPreloading
      };
    },

    // Нова функція для миттєвого застосування
    applyInstant(card) {
      return applyFromCache(card);
    }
  };

  // Експортуємо у window
  w[NS] = api;

  // ===== ІНІЦІАЛІЗАЦІЯ
  const boot = () => {
    console.log('[BOOT] ProductCards with preloading...');
    api.init();
  };

  if (d.readyState === 'loading') {
    d.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  // При завантаженні window - переконуємося що preload завершений
  w.addEventListener('load', () => {
    console.log('[LOAD] Window loaded, ensuring preload completion');
    if (!preloadComplete) {
      preloadAllCards();
    }
  }, { once: true });

  // Дебаг
  if (w.__CARD_DEBUG) {
    w.__cardDebug = api;
    console.log('Debug mode enabled. Use __cardDebug for debugging.');
  }

})(window, document);