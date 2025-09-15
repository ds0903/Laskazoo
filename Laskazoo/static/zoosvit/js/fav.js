// static/zoosvit/js/fav.js
(function () {
  'use strict';
  if (window.__favBound) return;
  window.__favBound = true;

  const BADGE_SEL = '[data-favs-count], .js-fav-count, .header-icon .icon-badge';

  // --- helpers ---------------------------------------------------------------
  function getCookie(name){
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }
  function getProdIdFromUrl(url=''){
    // /favourites/toggle/68/  або /favourites/toggle/68?...
    const m = String(url).match(/\/toggle\/(\d+)(?:[\/?]|$)/);
    return m ? Number(m[1]) : NaN;
  }
  function getProdId(btn){
    // пріоритет: data-product, далі з url
    const d = Number(btn?.dataset?.product);
    if (Number.isFinite(d)) return d;
    return getProdIdFromUrl(btn?.dataset?.url || btn?.getAttribute('data-url') || '');
  }
  function normBool(v){
    if (typeof v === 'boolean') return v;
    if (v == null) return false;
    const s = String(v).toLowerCase();
    return s === '1' || s === 'true' || s === 'on' || s === 'yes' || s === 'added' || s === 'active';
  }

  // глобальні набори
  window.__favVarSet  = window.__favVarSet  instanceof Set ? window.__favVarSet  : new Set();
  window.__favProdSet = window.__favProdSet instanceof Set ? window.__favProdSet : new Set();

  // --- core ------------------------------------------------------------------
  async function toggleFav(btn){
    let url = btn.dataset.url || '';
    const variantId = Number(btn.dataset.variant);
    const productId = getProdId(btn);

    // додаємо variant= тільки якщо він валідний (>0)
    if (Number.isFinite(variantId) && variantId > 0) {
      const sep = url.includes('?') ? '&' : '?';
      url = `${url}${sep}variant=${variantId}`;
    }
    if (!url) return;

    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');

    try {
      let resp = await fetch(url, {
        method:'POST',
        headers:{
          'X-Requested-With':'XMLHttpRequest',
          'X-CSRFToken': getCookie('csrftoken')
        },
        credentials:'same-origin'
      });
      if (resp.status === 405) {
        resp = await fetch(url, { method:'GET', credentials:'same-origin' });
      }
      const ct   = resp.headers.get('content-type') || '';
      const data = ct.includes('application/json') ? await resp.json() : {};

      // витягуємо ids з відповіді, fallback на те що було в кнопці
      const vIdRaw = (data.variant ?? data.variant_id ?? (Number.isFinite(variantId) ? variantId : null));
      const pIdRaw = (data.product ?? data.product_id ?? (Number.isFinite(productId) ? productId : null));
      const vId    = Number(vIdRaw);
      const pId    = Number(pIdRaw);

      // нормалізація стану
      let isOn = false;
      if ('state' in data)          isOn = normBool(data.state);
      else if ('status' in data)    isOn = normBool(data.status);
      else if ('added' in data)     isOn = normBool(data.added);
      else if ('active' in data)    isOn = normBool(data.active);
      else if ('is_on' in data)     isOn = normBool(data.is_on);
      else if ('favorited' in data) isOn = normBool(data.favorited);
      else                          isOn = !btn.classList.contains('is-on'); // оптимістично

      // 1) завжди оновлюємо саму натиснуту кнопку
      btn.classList.toggle('is-on', isOn);
      btn.setAttribute('aria-pressed', isOn ? 'true' : 'false');

      // 2) підтримуємо локальні набори
      if (Number.isFinite(vId) && vId > 0) {
        if (isOn) window.__favVarSet.add(vId); else window.__favVarSet.delete(vId);
      } else if (Number.isFinite(pId) && pId > 0) {
        if (isOn) window.__favProdSet.add(pId); else window.__favProdSet.delete(pId);
      }

      // 3) синхронізація інших кнопок на сторінці
      if (Number.isFinite(vId) && vId > 0) {
        // за варіантом
        document.querySelectorAll(`.js-fav[data-variant="${vId}"]`).forEach(b=>{
          b.classList.toggle('is-on', isOn);
          b.setAttribute('aria-pressed', isOn ? 'true' : 'false');
        });
      } else if (Number.isFinite(pId) && pId > 0) {
        // за продуктом (коли варіанту немає)
        document.querySelectorAll('.js-fav').forEach(b=>{
          const bp = getProdId(b);
          if (bp === pId) {
            b.classList.toggle('is-on', isOn);
            b.setAttribute('aria-pressed', isOn ? 'true' : 'false');
          }
        });
      }

      // 4) бейдж у шапці
      const badge = document.querySelector(BADGE_SEL);
      const count = Number.isInteger(data.count) ? data.count :
                    Number.isInteger(data.total) ? data.total : null;
      if (badge && count != null) {
        badge.textContent = String(count);
        badge.hidden = count <= 0;
      }

      // 5) якщо це сторінка «Обране» і ми зняли — видаляємо картку
      const favPage = document.querySelector('.favourites-page');
      if (favPage && !isOn) {
        const card = btn.closest('.prod-card');
        card?.remove();
        const grid = favPage.querySelector('.product-grid');
        if (grid && !grid.querySelector('.prod-card')) {
          grid.classList.add('is-empty');
          grid.innerHTML = '<p class="no-favourites">У вас поки що немає обраних товарів. ;(</p>';
        }
      }
    } finally {
      btn.disabled = false;
      btn.removeAttribute('aria-busy');
    }
  }

  // делегування кліку
  document.addEventListener('click', (e)=>{
    const btn = e.target.closest('.js-fav');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    toggleFav(btn);
  });

  // синхронізація стану при завантаженні (якщо є локальні set'и)
  document.addEventListener('DOMContentLoaded', ()=>{
    const favVar = window.__favVarSet  instanceof Set ? window.__favVarSet  : new Set();
    const favProd= window.__favProdSet instanceof Set ? window.__favProdSet : new Set();

    document.querySelectorAll('.prod-card').forEach(card=>{
      const favBtn = card.querySelector('.js-fav'); if (!favBtn) return;

      const pId = getProdId(favBtn);
      const vId = Number(favBtn.dataset.variant);

      let isOn = false;

      if (Number.isFinite(vId) && vId > 0 && favVar.has(vId)) {
        isOn = true;
      } else if (Number.isFinite(pId) && pId > 0 && favProd.has(pId)) {
        isOn = true;
      } else {
        // якщо у картці є пігулки — можливо улюблений варіант серед них
        const pills = Array.from(card.querySelectorAll('.variant-pill'));
        const pillVids = pills.map(p => Number(p.dataset.vid)).filter(Number.isFinite);
        isOn = pillVids.some(x => favVar.has(x));
        if (isOn && !Number.isFinite(vId)) {
          const matched = pillVids.find(x => favVar.has(x));
          if (Number.isFinite(matched)) favBtn.dataset.variant = String(matched);
        }
      }

      favBtn.classList.toggle('is-on', isOn);
      favBtn.setAttribute('aria-pressed', isOn ? 'true' : 'false');
    });
  });

})();
