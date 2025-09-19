// zoosvit/js/cart-modal.js
(() => {
  console.log('[cart-modal] v5 loaded - ВИПРАВЛЕННЯ ПОДВІЙНОГО ДОДАВАННЯ');

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
  console.log('[cart-modal] Оновлюємо бейдж кошика...');
  fetch(URLS.badge, {
    credentials: 'include',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
  .then(res => {
    console.log('[cart-modal] Відповідь від сервера для бейджа:', res.status);
    return res.ok ? res.json() : null;
  })
  .then(data => {
    if (!data) {
      console.warn('[cart-modal] Не отримано дані для бейджа');
      return;
    }

    const qty   = (data.qty ?? data.count ?? 0);
    const total = parseFloat(data.total ?? 0);
    const { countEl, totalEl } = getBadgeEls();

    console.log('[cart-modal] Дані бейджа:', { qty, total });

    if (countEl) {
      countEl.textContent = qty;
      console.log('[cart-modal] Оновлено лічильник:', qty);
    } else {
      console.warn('[cart-modal] Елемент .cart-count не знайдено');
    }

    if (totalEl) {
      if (total > 0) {
        totalEl.textContent = `${total.toFixed(2)} грн`;
        totalEl.hidden = false;
        console.log('[cart-modal] Оновлено суму:', total);
      } else {
        totalEl.textContent = '';
        totalEl.hidden = true;
        console.log('[cart-modal] Приховано суму (кошик порожній)');
      }
    } else {
      console.warn('[cart-modal] Елемент .cart-total не знайдено');
    }
  })
  .catch(e => {
    console.error('[cart-modal] Помилка оновлення бейджа:', e);
  });
}


  async function loadModal() {
    const r = await fetch(URLS.modal, { credentials:'include' });
    if (r.redirected) { location = r.url; return; }
    body.innerHTML = await r.text();
  }

  function openModal(){ overlay?.classList.remove('hidden'); document.documentElement.classList.add('no-scroll'); }
  function closeModal(){ overlay?.classList.add('hidden'); document.documentElement.classList.remove('no-scroll'); }

  // ----- cart add ----- КРИТИЧНЕ ВИПРАВЛЕННЯ ПОДВІЙНОГО ДОДАВАННЯ
  let addToCartClickTimes = {}; // захист від подвійних кліків на картках
  let processingButtons = new Set(); // додатковий захист для обробки кнопок
  
  document.addEventListener('click', async (e) => {
    const a = e.target.closest('a.add-to-cart');
    if (!a) return;
    e.preventDefault();
    
    // ПОКРАЩЕНИЙ ЗАХИСТ ВІД ПОДВІЙНИХ КЛІКІВ
    const buttonId = a.href + '_' + (a.dataset.variant || a.dataset.vid || 'default');
    const now = Date.now();
    
    // Перевіряємо, чи вже обробляється ця кнопка
    if (processingButtons.has(buttonId)) {
      console.log('ЗАХИСТ JS: Кнопка вже обробляється, ігноруємо');
      return;
    }
    
    // Перевіряємо часовий захист (зменшено з 3000 до 1500мс)
    if (addToCartClickTimes[buttonId] && (now - addToCartClickTimes[buttonId]) < 1500) {
      console.log('ЗАХИСТ JS: Подвійний клік на картці товару, ігноруємо');
      return;
    }
    
    // Реєструємо початок обробки
    addToCartClickTimes[buttonId] = now;
    processingButtons.add(buttonId);
    
    // Візуальний фідбек - робимо кнопку неактивною МИТТЄВО
    const originalText = a.textContent;
    const originalPointerEvents = a.style.pointerEvents;
    const originalOpacity = a.style.opacity;
    
    a.style.pointerEvents = 'none';
    a.style.opacity = '0.6';
    a.textContent = 'Додаємо...';
    a.disabled = true;
    
    // Функція відновлення кнопки
    const restoreButton = () => {
      a.style.pointerEvents = originalPointerEvents || '';
      a.style.opacity = originalOpacity || '';
      a.textContent = originalText;
      a.disabled = false;
      processingButtons.delete(buttonId);
      console.log(`ЗАВЕРШЕНО: ${buttonId} - кнопка знову активна`);
    };
    
    const url = a.href.includes('?') ? a.href + '&ajax=1' : a.href + '?ajax=1';
    try {
      console.log(`ДОДАЄМО ТОВАР: ${buttonId} - відправляємо запит`);
      const r = await fetch(url, { credentials:'include', headers:{'X-Requested-With':'XMLHttpRequest'} });
      
      if (r.status === 429) {
        // Якщо сервер заблокував - швидко відновлюємо кнопку
        console.log('Сервер заблокував запит (HTTP 429)');
        setTimeout(restoreButton, 500);
        return;
      }
      
      if (r.redirected) { 
        location = r.url; 
        return; 
      }
      
      if (r.ok) {
        console.log(`ТОВАР ДОДАНО: ${buttonId} - оновлюємо UI`);
        // Спочатку оновлюємо бейдж, потім модалку
        await refreshBadge();
        await loadModal();
        openModal();
        
        // Швидше відновлюємо кнопку після успішного додавання
        setTimeout(restoreButton, 800);
      } else {
        console.error('Помилка відповіді сервера:', r.status);
        setTimeout(restoreButton, 1000);
      }
    } catch(err){ 
      console.error('[cart-modal] add fail → fallback', err); 
      // При помилці відновлюємо кнопку швидше
      setTimeout(restoreButton, 1000);
      location = a.href; 
    }
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
  let lastClickTime = {}; // захист від подвійних кліків
  
  document.addEventListener('click', async (e) => {
    const link = e.target.closest('#cart-modal-body a.js-cart');
    if (!link) return;
    e.preventDefault();
    
    // ПОКРАЩЕНИЙ ЗАХИСТ ВІД ПОДВІЙНИХ КЛІКІВ
    const now = Date.now();
    const key = link.href;
    if (lastClickTime[key] && (now - lastClickTime[key]) < 1000) {
      console.log('ЗАХИСТ JS: Подвійний клік у модалці, ігноруємо');
      return;
    }
    lastClickTime[key] = now;
    
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
