// static/zoosvit/js/filters.js
window.applyFilters = function(){
  const url = new URL(window.location.href);
  url.searchParams.delete('brand');
  document.querySelectorAll('input[name="brand"]:checked')
    .forEach(cb => url.searchParams.append('brand', cb.value));
  const min = document.querySelector('input[name="price_min"]')?.value || '';
  const max = document.querySelector('input[name="price_max"]')?.value || '';
  const inStock = document.querySelector('input[name="in_stock"]')?.checked || false;
  if (min) url.searchParams.set('price_min', min); else url.searchParams.delete('price_min');
  if (max) url.searchParams.set('price_max', max); else url.searchParams.delete('price_max');
  if (inStock) url.searchParams.set('in_stock', '1'); else url.searchParams.delete('in_stock');
  window.location = url.toString();
};
