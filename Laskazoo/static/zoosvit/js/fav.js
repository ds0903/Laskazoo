// static/zoosvit/js/fav.js
(function () {
  'use strict';
  if (window.__favBound) return;
  window.__favBound = true;

  const BADGE_SEL = '[data-favs-count], .js-fav-count, .header-icon .icon-badge';

  function getCookie(name){
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }

  async function toggleFav(btn){
    let url = btn.dataset.url || '';
    const variantId = btn.dataset.variant;
    if (variantId) {
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
      const ct = resp.headers.get('content-type') || '';
      const data = ct.includes('application/json') ? await resp.json() : {};

      const vId = Number(data.variant || variantId);
      const isOn = data.state === 'added';

      if (!window.__favVarSet) window.__favVarSet = new Set();
      if (Number.isFinite(vId)) {
        if (isOn) window.__favVarSet.add(vId);
        else window.__favVarSet.delete(vId);
      }

      if (Number.isFinite(vId)) {
        // підсвітити ВСІ ❤️ із таким же exact-variant
        document.querySelectorAll(`.js-fav[data-variant="${vId}"]`).forEach(b=>{
          b.classList.toggle('is-on', isOn);
          b.setAttribute('aria-pressed', isOn ? 'true' : 'false');
        });

        // + якщо у картках є інші ❤️ цього ж продукту (з іншим data-variant),
        //   але їхні пігулки містять vId — теж синхронізуємо
        document.querySelectorAll('.prod-card').forEach(card=>{
          const favBtn = card.querySelector('.js-fav');
          if (!favBtn) return;
          // якщо вже збігається — скіпаємо
          if (Number(favBtn.dataset.variant) === vId) return;

          const anyMatch = Array.from(card.querySelectorAll('.variant-pill'))
                                .some(p => Number(p.dataset.vid) === vId);
          if (anyMatch) {
            favBtn.dataset.variant = String(vId);
            favBtn.classList.toggle('is-on', isOn);
            favBtn.setAttribute('aria-pressed', isOn ? 'true' : 'false');
          }
        });
      }

      const badge = document.querySelector(BADGE_SEL);
      const count = Number.isInteger(data.count) ? data.count :
                    Number.isInteger(data.total) ? data.total : null;
      if (badge && count != null) {
        badge.textContent = String(count);
        badge.hidden = count <= 0;
      }

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

  document.addEventListener('click', (e)=>{
    const btn = e.target.closest('.js-fav');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    toggleFav(btn);
  });

  // 🔥 ГОЛОВНЕ: синхронізувати ❤️ на новій сторінці, навіть якщо data-variant ≠ улюблений варіант
  document.addEventListener('DOMContentLoaded', ()=>{
    const favSet = window.__favVarSet instanceof Set ? window.__favVarSet : new Set();

    document.querySelectorAll('.prod-card').forEach(card=>{
      const favBtn = card.querySelector('.js-fav');
      if (!favBtn) return;

      const currentVid = Number(favBtn.dataset.variant);
      const pills = Array.from(card.querySelectorAll('.variant-pill'));
      const pillVids = pills.map(p => Number(p.dataset.vid)).filter(Number.isFinite);

      // якщо поточний variant у сеті — просто підсвітити
      if (Number.isFinite(currentVid) && favSet.has(currentVid)) {
        favBtn.classList.add('is-on');
        favBtn.setAttribute('aria-pressed', 'true');
        return;
      }

      // інакше — шукаємо "будь-який" улюблений варіант серед пігулок цього продукту
      const matched = pillVids.find(v => favSet.has(v));
      if (Number.isFinite(matched)) {
        favBtn.dataset.variant = String(matched); // щоб наступний клік працював по улюбленому
        favBtn.classList.add('is-on');
        favBtn.setAttribute('aria-pressed', 'true');
      } else {
        // якщо немає збігів — вимикаємо (на випадок, коли юзер видалив з обраного)
        favBtn.classList.remove('is-on');
        favBtn.setAttribute('aria-pressed', 'false');
      }
    });
  });
})();
