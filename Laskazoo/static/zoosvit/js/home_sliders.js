(function () {
  'use strict';
  const $all = (s, r=document) => Array.from(r.querySelectorAll(s));

  /* ---------- product slider ---------- */
  function initProductSlider() {
    const w = document.querySelector('.product-slider');
    if (!w) return;
    const slider   = w.querySelector('.grid-slider');
    const leftBtn  = w.querySelector('.slide-btn.left');
    const rightBtn = w.querySelector('.slide-btn.right');

    const css   = getComputedStyle(document.documentElement);
    const cardW = parseInt(css.getPropertyValue('--prod-card-width'),10);
    const gap   = parseInt(css.getPropertyValue('--prod-gap'),10);
    const perV  = parseInt(css.getPropertyValue('--prod-per-page'),10);
    const perS  = parseInt(css.getPropertyValue('--prod-scroll'),10);
    const total = w.querySelectorAll('.prod-card').length;

    const maxPage = Math.max(0, Math.ceil((total - perV) / perS));
    let page = 0;

    function go(delta){
      page = Math.min(maxPage, Math.max(0, page + delta));
      slider.style.transform = `translateX(-${page * perS * (cardW + gap)}px)`;
      leftBtn.style.display  = page === 0 ? 'none' : 'block';
      rightBtn.style.display = page >= maxPage ? 'none' : 'block';
      if (typeof window.recomputeCardHeights === 'function') {
        requestAnimationFrame(window.recomputeCardHeights);
      }
    }
    leftBtn?.addEventListener('click',  ()=>go(-1));
    rightBtn?.addEventListener('click', ()=>go(+1));
    leftBtn && (leftBtn.style.display = 'none');
    rightBtn && (rightBtn.style.display = maxPage ? 'block':'none');
  }

  /* ---------- hero carousel ---------- */
  function initHeroCarousel() {
    const slides = $all('.carousel-slide');
    const nav    = document.querySelector('.carousel-nav');
    if (!slides.length || !nav) {
      // без навігації просто показати перший слайд
      slides[0]?.classList.add('active');
      return;
    }
    const D = 5000; let i = 0, t;

    slides.forEach((_, idx)=>{
      const bar = document.createElement('div');
      bar.className='nav-bar'; bar.innerHTML='<div class="bar-progress"></div>';
      bar.addEventListener('click', ()=>show(idx));
      nav.appendChild(bar);
    });
    const bars = $all('.nav-bar', nav);

    function show(idx){
      slides.forEach(s=>s.classList.remove('active'));
      bars.forEach(b=>{
        b.classList.remove('active');
        b.querySelector('.bar-progress').style.animation='none';
      });
      i = idx;
      slides[i].classList.add('active');
      const bar = bars[i];
      bar.classList.add('active');
      // перезапуск анімації
      bar.querySelector('.bar-progress').offsetWidth; // reflow
      bar.querySelector('.bar-progress').style.animation=`fillBar ${D}ms linear forwards`;
      clearTimeout(t); t=setTimeout(()=>show((i+1)%slides.length), D);
    }
    show(0);
    
    // Клік по банеру з посиланням
    slides.forEach(slide => {
      const link = slide.dataset.link;
      if (link) {
        slide.style.cursor = 'pointer';
        slide.addEventListener('click', () => {
          window.location.href = link;
        });
      }
    });
  }

  /* ---------- category slider ---------- */
  function initCategorySlider() {
    const w = document.querySelector('.category-slider');
    if (!w) return;

    const slider   = w.querySelector('.grid-slider');
    const leftBtn  = w.querySelector('.slide-btn.left');
    const rightBtn = w.querySelector('.slide-btn.right');

    const css   = getComputedStyle(document.documentElement);
    const cardW = parseInt(css.getPropertyValue('--cat-card-width'),10);
    const gap   = parseInt(css.getPropertyValue('--cat-gap'),10);
    const perV  = parseInt(css.getPropertyValue('--cat-per-page'),10);
    const perS  = parseInt(css.getPropertyValue('--cat-scroll'),10);
    const total = w.querySelectorAll('.cat-card').length;

    if (total <= perV || total === 0) {
      w.classList.add('centered');
      if (slider) slider.style.transform = 'none';
      leftBtn && (leftBtn.style.display = 'none');
      rightBtn && (rightBtn.style.display = 'none');
      return;
    }

    const maxPage = Math.max(0, Math.ceil((total - perV) / perS));
    let page = 0;

    function go(delta){
      page = Math.min(maxPage, Math.max(0, page + delta));
      slider.style.transform = `translateX(-${page * perS * (cardW + gap)}px)`;
      leftBtn.style.display  = page === 0 ? 'none' : 'block';
      rightBtn.style.display = page >= maxPage ? 'none' : 'block';
    }
    leftBtn?.addEventListener('click',  ()=>go(-1));
    rightBtn?.addEventListener('click', ()=>go(+1));
    leftBtn && (leftBtn.style.display = 'none');
    rightBtn && (rightBtn.style.display = maxPage ? 'block':'none');
  }

  /* ---------- brands “show more” ---------- */
  function initBrandsToggle(){
    const section = document.getElementById('brands');
    const grid    = section?.querySelector('.brands-grid.extra');
    const btn     = document.getElementById('toggle-brands');
    if (!section || !grid || !btn) return;

    btn.addEventListener('click', ()=>{
      const collapsed = section.classList.contains('collapsed');
      grid.style.transition = `max-height 0.3s ${collapsed ? 'ease-out' : 'ease-in'}`;
      grid.style.maxHeight  = collapsed ? grid.scrollHeight + 'px' : '0px';
      btn.textContent       = collapsed ? 'Згорнути' : 'Показати ще';
      section.classList.toggle('collapsed');
    });
  }

  /* ---------- entry ---------- */
  document.addEventListener('DOMContentLoaded', ()=>{
    initProductSlider();
    initHeroCarousel();
    initCategorySlider();
    initBrandsToggle();

    // звести посилання під кнопками на бек-стороні
    document.querySelectorAll('.prod-card .card-back a').forEach(a=>{
      a.style.position = 'relative'; a.style.zIndex = 1;
    });
  });
})();
