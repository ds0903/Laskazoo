/* static/zoosvit/js/product_cards.js */
(function (w, d) {
  'use strict';

  // ===== Налаштування
  const EXTRA_BUFFER = 30;                 // додатковий запас у px
  const MEASURE_CLASS = 'is-measuring';    // технічний клас для виміру
  const NS = 'ProductCards';               // ім'я простору у window

  // ===== Стан/кеш
  const heightCache = new WeakMap();

  // ===== Допоміжні
  const readLimits = () => {
    const CSS = getComputedStyle(d.documentElement);
    const MIN = parseInt(CSS.getPropertyValue('--prod-min-height')) || 320;
    const MAX = parseInt(CSS.getPropertyValue('--prod-max-height')) || 820;
    return { MIN, MAX };
  };
  const clampH = (v, MIN, MAX) => Math.min(MAX, Math.max(MIN, Math.max(0, v)));

  // одноразова інʼєкція стилю для «in-place» виміру
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

  // ===== Вимір однієї картки
  function measureCard(card){
    if (!card) return;

    // 1) пам'ятковий кеш
    if (heightCache.has(card)) {
      const h = heightCache.get(card);
      card.style.setProperty('--hover-height', h + 'px');
      return h;
    }

    // 2) кеш із data-атрибуту
    const ds = parseInt(card.dataset.hoverH || '0');
    const { MIN, MAX } = readLimits();
    if (ds) {
      const h = clampH(ds, MIN, MAX);
      heightCache.set(card, h);
      card.style.setProperty('--hover-height', h + 'px');
      return h;
    }

    const back = card.querySelector('.card-back');
    if (!back) return;

    // страхуємо scrollHeight, якщо зображення ще не завантажились
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

    // вимір
    card.classList.add(MEASURE_CLASS);

    let desired = back.scrollHeight;
    const last = back.lastElementChild;
    if (last) {
      desired += parseFloat(getComputedStyle(last).marginBottom) || 0;
    }
    desired = Math.ceil(desired + EXTRA_BUFFER); // ← загальний запас

    card.classList.remove(MEASURE_CLASS);

    const h = clampH(desired, MIN, MAX);

    // дебаг: позначаємо картки, що вперлись у MAX
    if (w.__CARD_DEBUG) {
      if (h < desired) card.dataset.clamped = '1';
      else card.removeAttribute('data-clamped');
    }

    heightCache.set(card, h);
    card.dataset.hoverH = String(h);
    card.style.setProperty('--hover-height', h + 'px');
    return h;
  }

  // ===== Ледачий вимір усіх карток
  function measureAll(){
    const cards = d.querySelectorAll('.prod-card');
    if (!('IntersectionObserver' in w)) {
      cards.forEach(measureCard);
      return;
    }
    const io = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{
        if (e.isIntersecting) {
          measureCard(e.target);
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: '300px 0px' });
    cards.forEach(c=>io.observe(c));
  }

  // ===== Пігулки варіантів
  function initVariantPills(ctx = d){
    ctx.querySelectorAll('.prod-card').forEach(card=>{
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

      const setText = (el, t)=>{ if (el) el.textContent = t; };
      const suffix  = (p)=> {
        const w = p.dataset.weight; const s = p.dataset.size;
        if (w && !isNaN(Number(w))) return ` — ${Number(w)} кг`;
        if (s) return ` — ${s}`;
        return '';
      };

      function apply(pill){
        pills.forEach(b=>b.classList.remove('active'));
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
        if (price){ setText(priceF, `₴ ${price}`); setText(priceB, `₴ ${price}`); }

        if (titleF) titleF.textContent = baseTitle + suffix(pill);
        if (titleB) titleB.textContent = baseTitle + suffix(pill);

        if (addBtn && addBase) addBtn.href = `${addBase}?variant=${vid}`;

        if (favBtn) {
          favBtn.dataset.variant = vid;
          const isOn = !!(w.__favVarSet && w.__favVarSet.has(Number(vid)));
          favBtn.classList.toggle('is-on', isOn);
          favBtn.setAttribute('aria-pressed', isOn ? 'true' : 'false');
        }

        // після зміни — переміряти конкретну картку
        api.recomputeOneCard(card);
      }

      pills.forEach(p=>p.addEventListener('click', e=>{
        e.preventDefault(); e.stopPropagation(); apply(p);
      }));

      apply(pills[0]); // початковий стан
    });
  }

  // ===== Публічне API
  const api = {
    init(ctx){ initVariantPills(ctx || d); measureAll(); },
    measureAll,
    recomputeOneCard(card){
      if (!card) return;
      heightCache.delete(card);
      delete card.dataset.hoverH;
      requestAnimationFrame(()=>measureCard(card));
    }
  };

  // Експортуємо у window
  w[NS] = api;

  // ===== Хуки життєвого циклу
  const boot = () => api.init();
  if (d.readyState === 'loading') {
    d.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
  // додаткові уточнення коли все завантажилось
  w.addEventListener('load', api.measureAll, { once:true });
  if (d.fonts?.ready) d.fonts.ready.then(api.measureAll);

  // коли завантажилась будь-яка картинка — переміряти її картку
  d.addEventListener('load', (e)=>{
    const img = e.target;
    if (!(img instanceof HTMLImageElement)) return;
    const card = img.closest('.prod-card');
    if (!card) return;
    api.recomputeOneCard(card);
  }, true);

})(window, document);
