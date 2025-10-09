// static/zoosvit/js/filters.js

// Функція застосування фільтрів
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

// Автоматичне застосування фільтрів при зміні
document.addEventListener('DOMContentLoaded', function() {
  // Чекбокси брендів - застосовувати одразу
  document.querySelectorAll('input[name="brand"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      applyFilters();
    });
  });

  // Чекбокс "В наявності" - застосовувати одразу
  const inStockCheckbox = document.querySelector('input[name="in_stock"]');
  if (inStockCheckbox) {
    inStockCheckbox.addEventListener('change', function() {
      applyFilters();
    });
  }

  // Інпути ціни - застосовувати з невеликою затримкою (debounce)
  let priceTimeout;
  document.querySelectorAll('input[name="price_min"], input[name="price_max"]').forEach(input => {
    input.addEventListener('input', function() {
      clearTimeout(priceTimeout);
      priceTimeout = setTimeout(() => {
        applyFilters();
      }, 800); // затримка 800мс після останнього введення
    });
  });
});
