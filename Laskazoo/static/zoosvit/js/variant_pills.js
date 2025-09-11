(function () {
  'use strict';

  function initVariantPills(ctx = document){
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
      const addBase = addBtn ? (addBtn.dataset.addBase || addBtn.href.split('?')[0]) : '';

      const baseTitle = (titleF?.dataset.baseTitle || titleF?.textContent || '').trim();

      const setText = (el, t)=>{ if (el) el.textContent = t; };
      const suffix  = (p)=>{
        const w = p.dataset.weight, s = p.dataset.size;
        if (w && !isNaN(Number(w))) return ` — ${Number(w)} кг`;
        if (s) return ` — ${s}`;
        return '';
      };

      function apply(pill){
        pills.forEach(b=>b.classList.remove('active'));
        pill.classList.add('active');

        const img   = pill.dataset.image;
        const sku   = pill.dataset.sku || '—';
        const price = pill.dataset.retail_price || pill.dataset.price; // на різних сторінках різні атрибути
        const vid   = pill.dataset.vid;

        if (img) {
          // акуратно без кеш-стрибків
          const src = `${img}${img.includes('?') ? '&' : '?'}v=${vid}`;
          if (imgF) { imgF.removeAttribute('srcset'); imgF.src = src; }
          if (imgB) { imgB.removeAttribute('srcset'); imgB.src = src; }
        }

        setText(skuF, `Артикул: ${sku}`);
        setText(skuB, `Артикул: ${sku}`);

        if (price){
          setText(priceF, `₴ ${price}`);
          setText(priceB, `₴ ${price}`);
        }

        if (titleF) titleF.textContent = baseTitle + suffix(pill);
        if (titleB) titleB.textContent = baseTitle + suffix(pill);

        if (addBtn && addBase) addBtn.href = `${addBase}?variant=${vid}`;

        // ❤️
        const favBtn = card.querySelector('.js-fav');
        if (favBtn) {
          favBtn.dataset.variant = vid;
          const isOn = !!(window.__favVarSet && window.__favVarSet.has(Number(vid)));
          favBtn.classList.toggle('is-on', isOn);
          favBtn.setAttribute('aria-pressed', isOn ? 'true' : 'false');
        }

        if (typeof window.recomputeCardHeights === 'function') {
          requestAnimationFrame(window.recomputeCardHeights);
        }
      }

      pills.forEach(p=>p.addEventListener('click', e=>{
        e.preventDefault(); e.stopPropagation(); apply(p);
      }));

      apply(pills[0]); // первинний стан
    });
  }

  document.addEventListener('DOMContentLoaded', ()=>initVariantPills());
  window.initVariantPills = initVariantPills; // якщо десь знадобиться вручну
})();
