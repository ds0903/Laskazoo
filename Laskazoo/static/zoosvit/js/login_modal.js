document.addEventListener('DOMContentLoaded', () => {
  // DOM елементи
  const modal = document.getElementById('auth-modal');
  const closeBtn = modal?.querySelector('.auth-close-btn');
  const headerLoginBtn = document.getElementById('open-login-modal');
  const headerRegBtn = document.getElementById('open-register-modal');
  const tabs = document.querySelectorAll('.auth-tab');
  const loginBox = document.getElementById('login-form');
  const registerBox = document.getElementById('register-form');

  if (!modal) return;

  // Функція для очищення форми
  function clearForm(formElement) {
    if (!formElement) return;
    
    const form = formElement.querySelector('form');
    if (form) {
      // Очищуємо всі input поля
      const inputs = form.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
      inputs.forEach(input => {
        input.value = '';
        input.classList.remove('error'); // видаляємо класи помилок якщо є
      });
      
      // Видаляємо повідомлення про помилки
      const errorMessages = form.querySelectorAll('.error-message, .errorlist, .non-field-errors');
      errorMessages.forEach(error => error.remove());
      
      // Видаляємо класи помилок з полів
      const fieldGroups = form.querySelectorAll('.form-group');
      fieldGroups.forEach(group => group.classList.remove('has-error'));
      
      // Видаляємо атрибути aria-invalid
      const invalidFields = form.querySelectorAll('[aria-invalid="true"]');
      invalidFields.forEach(field => field.removeAttribute('aria-invalid'));
    }
  }

  // Функція для скидання всіх форм в модалці
  function clearAllForms() {
    clearForm(loginBox);
    clearForm(registerBox);
  }

  // Функція для показу потрібної вкладки
  function showTab(name) {
    const isLogin = name === 'login';
    if (loginBox) loginBox.style.display = isLogin ? 'block' : 'none';
    if (registerBox) registerBox.style.display = isLogin ? 'none' : 'block';
    
    tabs.forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === name);
    });
  }

  // Функція для закриття модалки
  function closeModal() {
    modal.classList.remove('show');
    // Скидаємо стан всіх форм при закритті
    clearAllForms();
  }

  // Клики по вкладках усередині модалки
  tabs.forEach(tab => {
    tab.addEventListener('click', e => {
      e.preventDefault();
      // Очищуємо форми при переключенні вкладок
      clearAllForms();
      showTab(tab.dataset.tab);
    });
  });

  // Клики на кнопки в header
  if (headerLoginBtn) {
    headerLoginBtn.addEventListener('click', e => {
      e.preventDefault();
      clearAllForms();
      showTab('login');
      modal.classList.add('show');
    });
  }

  if (headerRegBtn) {
    headerRegBtn.addEventListener('click', e => {
      e.preventDefault();
      clearAllForms();
      showTab('register');
      modal.classList.add('show');
    });
  }

  // Закрити модалку
  if (closeBtn) {
    closeBtn.addEventListener('click', closeModal);
  }

  // Закрити модалку при кліку поза нею
  modal.addEventListener('click', e => {
    if (e.target === modal) {
      closeModal();
    }
  });

  // Закрити модалку при натисканні Escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && modal.classList.contains('show')) {
      closeModal();
    }
  });

  // AJAX submit для обох форм
  document.body.addEventListener('submit', async e => {
    const form = e.target;
    
    // Ловимо тільки наші дві форми
    if (form.id !== 'login-form-ajax' && form.id !== 'register-form-ajax') return;

    e.preventDefault();
    
    // Показуємо індикатор завантаження
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Обробка...';
    }

    try {
      const data = new FormData(form);
      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'X-CSRFToken': data.get('csrfmiddlewaretoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: data
      });

      if (response.ok) {
        // При успішному логіні/реєстрації - редірект
        const json = await response.json();
        if (json.redirect_url) {
          window.location.href = json.redirect_url;
        } else {
          // Якщо немає redirect_url, закриваємо модалку
          closeModal();
          window.location.reload(); // або оновлюємо сторінку
        }
      } else {
        // При помилці - вкидаємо назад HTML фрагмент форми
        const html = await response.text();
        const targetBox = form.id === 'login-form-ajax' ? loginBox : registerBox;
        
        if (targetBox) {
          targetBox.innerHTML = html;
          // Після заміни вмісту показуємо поточну вкладку
          showTab(form.id === 'login-form-ajax' ? 'login' : 'register');
        }
      }
    } catch (error) {
      console.error('Помилка при відправці форми:', error);
      
      // Показуємо загальну помилку користувачу
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message';
      errorDiv.textContent = 'Виникла помилка. Спробуйте ще раз.';
      form.insertBefore(errorDiv, form.firstChild);
      
    } finally {
      // Відновлюємо кнопку submit
      if (submitBtn && originalText) {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    }
  });

  // За замовчуванням показуємо вкладку логін
  showTab('login');
});
