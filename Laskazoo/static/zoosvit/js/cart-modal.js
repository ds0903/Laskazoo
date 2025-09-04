// zoosvit/js/cart-modal.js
(() => {
  console.log('[cart-modal] v4 loaded');

  const qs = (s, r=document) => r.querySelector(s);
  const overlay = qs('#cart-modal');
  const body    = qs('#cart-modal-body');

  const URLS = {
    modal: (window.ZOOSVIT_URLS && window.ZOOSVIT_URLS.cartModal) || '/orders/api/cart-modal/',
    badge: (window.ZOOSVIT_URLS && window.ZOOSVIT_URLS.cartCount) || '/orders/api/cart-count/',
    setQty: (itemId) => `/orders/item/${itemId}/set-qty/`,
  };

  const fmtUAH = v => new Intl.NumberFormat('uk-UA', {
    style:'currency', currency:'UAH', maximumFractionDigits:2
  }).format(Number(v || 0));

  function getBadgeEls() {
    return {
      countEl: document.querySelector('.cart-count'),
      totalEl: document.querySelector('.cart-total'),
    };
  }

  function refreshBadge() {
  fetch(URLS.badge, {
    credentials: 'include',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
  .then(res => res.ok ? res.json() : null)
  .then(data => {
    if (!data) return;

    const qty   = (data.qty ?? data.count ?? 0);
    const total = parseFloat(data.total ?? 0);
    const { countEl, totalEl } = getBadgeEls();

    if (countEl) countEl.textContent = qty;

    if (totalEl) {
      if (total > 0) {
        totalEl.textContent = `${total.toFixed(2)} грн`;
        totalEl.hidden = false;
      } else {
        totalEl.textContent = '';
        totalEl.hidden = true;
      }
    }
  })
  .catch(e => console.warn('[cart-modal] refresh badge error', e));
}


  async function loadModal() {
    const r = await fetch(URLS.modal, { credentials:'include' });
    if (r.redirected) { location = r.url; return; }
    body.innerHTML = await r.text();
  }

  function openModal(){ overlay?.classList.remove('hidden'); document.documentElement.classList.add('no-scroll'); }
  function closeModal(){ overlay?.classList.add('hidden'); document.documentElement.classList.remove('no-scroll'); }

  // ----- cart add -----
  document.addEventListener('click', async (e) => {
    const a = e.target.closest('a.add-to-cart');
    if (!a) return;
    e.preventDefault();
    const url = a.href.includes('?') ? a.href + '&ajax=1' : a.href + '?ajax=1';
    try {
      const r = await fetch(url, { credentials:'include', headers:{'X-Requested-With':'XMLHttpRequest'} });
      if (r.redirected) { location = r.url; return; }
      await refreshBadge();
      await loadModal();
      openModal();
    } catch(err){ console.error('[cart-modal] add fail → fallback', err); location = a.href; }
  });

  // ----- open modal from header -----
  document.addEventListener('click', async (e) => {
    const cartBtn = e.target.closest('a.btn-cart');
    if (!cartBtn) return;
    e.preventDefault();
    await loadModal();
    openModal();
  });

  // ----- close modal -----
  document.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.closest('.cm-close')) closeModal();
  });

  // ----- plus/minus/remove/clear inside modal -----
  document.addEventListener('click', async (e) => {
    const link = e.target.closest('#cart-modal-body a.js-cart');
    if (!link) return;
    e.preventDefault();
    try {
      const r = await fetch(link.href, { credentials:'include', headers:{'X-Requested-With':'XMLHttpRequest'} });
      if (r.redirected) { location = r.url; return; }
      body.innerHTML = await r.text();
      await refreshBadge();
    } catch(err){ console.error('[cart-modal] op fail → fallback', err); location = link.href; }
  });

  // ====== editable quantity (input) ======
  const getCSRF = () =>
    document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';

  const debounce = (fn, ms=350) => { let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), ms); }; };

  async function setQty(itemId, qty) {
    const r = await fetch(URLS.setQty(itemId), {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type':'application/x-www-form-urlencoded',
        'X-Requested-With':'XMLHttpRequest',
        'X-CSRFToken': getCSRF()
      },
      body: new URLSearchParams({ qty: String(qty) })
    });
    if (r.redirected) { location = r.url; return; }
    body.innerHTML = await r.text();
    await refreshBadge();
  }

  const onQtyInput = debounce(async (e) => {
    const inp = e.target;
    if (!inp.matches('#cart-modal-body input.cm-qty-input')) return;

    let val = parseInt(inp.value, 10);
    if (Number.isNaN(val)) return;         // чекаємо поки користувач вводить
    if (val < 1) val = 1;

    const max = inp.getAttribute('max');
    if (max) val = Math.min(val, parseInt(max, 10));

    inp.value = val;                        // нормалізуємо
    await setQty(inp.dataset.item, val);
  }, 400);

  document.addEventListener('input', onQtyInput);

  document.addEventListener('keydown', async (e) => {
    const inp = e.target;
    if (inp.matches('#cart-modal-body input.cm-qty-input') && e.key === 'Enter') {
      e.preventDefault();
      let v = parseInt(inp.value, 10); if (Number.isNaN(v) || v < 1) v = 1;
      await setQty(inp.dataset.item, v);
    }
  });

  document.addEventListener('change', async (e) => {
    const inp = e.target;
    if (!inp.matches('#cart-modal-body input.cm-qty-input')) return;
    let v = parseInt(inp.value, 10); if (Number.isNaN(v) || v < 1) v = 1;
    await setQty(inp.dataset.item, v);
  });

  // первинне оновлення бейджа
  document.addEventListener('DOMContentLoaded', refreshBadge);
})();

fetch(btn.href, {
  method: 'POST',
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': getCookie('csrftoken'),
  }
})
.then(res => res.json())
.then(data => {
  if (data.ok) {
    updateCartBadge(data.qty);           // оновлення бейджика
    updateCartTotal(data.total);         // ✅ нова функція!
  }
})
.catch(console.error);
