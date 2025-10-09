document.addEventListener('DOMContentLoaded', () => {
  // DOM елементи
  const modal = document.getElementById('auth-modal');
  const closeBtn = modal?.querySelector('.auth-close-btn');
  const tabs = document.querySelectorAll('.auth-tab');
  const loginBox = document.getElementById('login-form');
  const registerBox = document.getElementById('register-form');

  if (!modal) return;

  // Флаг для запобігання подвійній відправці
  let isSubmitting = false;

  // Функція для очищення форми
  function clearForm(formElement) {
    if (!formElement) return;
    
    const form = formElement.querySelector('form');
    if (form) {
      // Очищуємо всі input поля
      const inputs = form.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
      inputs.forEach(input => {
        input.value = '';
        input.classList.remove('error');
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
    isSubmitting = false;
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
    clearAllForms();
  }

  // Глобальні функції для відкриття модалки (доступні з header.html)
  window.openLoginModal = function() {
    clearAllForms();
    showTab('login');
    modal.classList.add('show');
  };

  window.openRegisterModal = function() {
    clearAllForms();
    showTab('register');
    modal.classList.add('show');
  };

  // Клики по вкладках усередині модалки
  tabs.forEach(tab => {
    tab.addEventListener('click', e => {
      e.preventDefault();
      clearAllForms();
      showTab(tab.dataset.tab);
    });
  });

  // Закрити модалку
  if (closeBtn) {
    closeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      closeModal();
    });
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
    
    // Запобігаємо подвійній відправці
    if (isSubmitting) {
      console.log('Форма вже відправляється, зачекайте...');
      return;
    }
    
    isSubmitting = true;
    
    // Показуємо індикатор завантаження
    const submitBtn = form.querySelector('button[type="submit"]');
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
        const json = await response.json();
        if (json.redirect_url) {
          window.location.href = json.redirect_url;
          return;
        } else {
          closeModal();
          window.location.reload();
          return;
        }
      } else {
        // При помилці - оновлюємо HTML форми (новий HTML вже має правильну кнопку)
        const html = await response.text();
        const targetBox = form.id === 'login-form-ajax' ? loginBox : registerBox;
        
        if (targetBox) {
          targetBox.innerHTML = html;
        }
        
        // Скидаємо флаг, щоб дозволити нову спробу
        isSubmitting = false;
      }
    } catch (error) {
      console.error('Помилка при відправці форми:', error);
      
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message';
      errorDiv.textContent = 'Виникла помилка. Спробуйте ще раз.';
      form.insertBefore(errorDiv, form.firstChild);
      
      // Дозволяємо спробувати ще раз
      isSubmitting = false;
      
      // Відновлюємо кнопку submit
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Зареєструватись';
      }
    }
  });

  // За замовчуванням показуємо вкладку логін
  showTab('login');
  
  // Підключаємо обробник для іконки користувача (неавторизовані)
  const userLoginBtn = document.getElementById('user-login-btn');
  if (userLoginBtn) {
    userLoginBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      window.openLoginModal();
    });
  }
});
