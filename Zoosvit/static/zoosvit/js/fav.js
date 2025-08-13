// static/zoosvit/js/fav.js
(function () {
  'use strict';
  if (window.__favBound) return;  // ⛔️ не вішати слухач двічі
  window.__favBound = true;

  const BADGE_SEL = '[data-favs-count], .js-fav-count, .header-icon .icon-badge';

  function getCookie(name){
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }

  async function toggleFav(btn){
    const url = btn.dataset.url;
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

      const isOn = !!(data.added ?? data.active ?? !btn.classList.contains('is-on'));

      // 🔴 єдиний істинний клас стану
      btn.classList.toggle('is-on', isOn);
      btn.setAttribute('aria-pressed', isOn ? 'true' : 'false');
      btn.classList.toggle('active', isOn); // сумісність, якщо десь ще є .active

      // бейдж у шапці
      const badge = document.querySelector(BADGE_SEL);
      const count = Number.isInteger(data.count) ? data.count :
                    Number.isInteger(data.total) ? data.total : null;
      if (badge && count != null) {
        badge.textContent = count;
        badge.hidden = count <= 0;
      }

      // якщо ми на сторінці обраного і знято — прибрати картку
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

  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('.js-fav').forEach(b=>{
      const on = b.getAttribute('aria-pressed') === 'true' || b.classList.contains('active');
      b.classList.toggle('is-on', on);
      b.classList.toggle('active', on);
    });
  });
})();

