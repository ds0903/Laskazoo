document.addEventListener('DOMContentLoaded', () => {
  const modal        = document.getElementById('auth-modal');
  const closeBtn     = document.querySelector('.auth-close-btn');
  const loginBtn     = document.getElementById('open-login-modal');
  const registerBtn  = document.getElementById('open-register-modal');
  const loginHdrBtn  = document.getElementById('open-login-modal');     // у хедері
  const registerHdrBtn = document.getElementById('open-register-modal'); // у хедері

  const loginForm    = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');

  const loginTab     = document.querySelector('[data-tab="login"]');
  const registerTab  = document.querySelector('[data-tab="register"]');

  if (!modal || !loginBtn || !registerBtn || !loginForm || !registerForm) return;

  // ✅ Вхід
  loginBtn.addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.style.display = 'block';
    registerForm.style.display = 'none';
    loginTab.classList.add('active');
    registerTab.classList.remove('active');
    modal.classList.add('show');
  });

  // ✅ Реєстрація
  registerBtn.addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.style.display = 'none';
    registerForm.style.display = 'block';
    loginTab.classList.remove('active');
    registerTab.classList.add('active');
    modal.classList.add('show');
  });

  // кліки по самим вкладкам у модалці
  loginTab.addEventListener('click', (e) => {
    e.preventDefault();
    showTab('login');
  });
  registerTab.addEventListener('click', (e) => {
    e.preventDefault();
    showTab('register');
  });

  // Закриття модалки
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('show');
  });
});



// розібрати потім потрібно буде
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('register-form-ajax');

  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(form);
    const response = await fetch(form.action, {
      method: 'POST',
      headers: {
        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    });

    if (response.ok) {
      const json = await response.json();
      window.location.href = json.redirect_url;
    } else {
      const html = await response.text();
      document.getElementById('register-form').innerHTML = html;
    }
  });

  // делегований слухач на submit для обох форм
  document.body.addEventListener('submit', async e => {
    const form = e.target;
    if (form.id === 'login-form-ajax' || form.id === 'register-form-ajax') {
      e.preventDefault();
      const formData = new FormData(form);
      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
      });

      if (response.ok) {
        // якщо успіх — нічної вставки, а редірект
        const json = await response.json();
        window.location.href = json.redirect_url;
      } else {
        // якщо помилка — вставляємо HTML фрагмент
        const html = await response.text();
        const targetId = form.id === 'login-form-ajax' ? 'login-form' : 'register-form';
        document.getElementById(targetId).innerHTML = html;
      }
    }
  });
});

document.getElementById('register-form-ajax')

document.addEventListener('DOMContentLoaded', () => {
  // знайдемо всі потрібні елементи
  const tabs          = document.querySelectorAll('.auth-tab');
  const loginFormDiv  = document.getElementById('login-form');
  const regFormDiv    = document.getElementById('register-form');

  function showTab(name) {
    if (name === 'login') {
      loginFormDiv.style.display  = 'block';
      regFormDiv.style.display    = 'none';
    } else {
      loginFormDiv.style.display  = 'none';
      regFormDiv.style.display    = 'block';
    }
    // підсвічуємо активну вкладку
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  }

  // повісимо слухач на всі кнопки .auth-tab
  tabs.forEach(tab => {
    tab.addEventListener('click', e => {
      e.preventDefault();
      showTab(tab.dataset.tab);
    });
  });

  // за замовчуванням можна показати login або register
  showTab('login');  // або 'register', якщо хочете щоб модалка завжди відкривалася на реєстрації
});

//
// розібрати код
//

document.addEventListener('DOMContentLoaded', () => {
  // --- 1) DOM-елементи ---
  const modal           = document.getElementById('auth-modal');
  const closeBtn        = modal.querySelector('.auth-close-btn');
  const headerLoginBtn  = document.getElementById('open-login-modal');
  const headerRegBtn    = document.getElementById('open-register-modal');
  const tabs            = document.querySelectorAll('.auth-tab');
  const loginBox        = document.getElementById('login-form');
  const registerBox     = document.getElementById('register-form');

  // --- 2) Функція для показу потрібної вкладки ---
  function showTab(name) {
    const isLogin = name === 'login';
    loginBox.style.display    = isLogin ? 'block' : 'none';
    registerBox.style.display = isLogin ? 'none'  : 'block';
    tabs.forEach(tab =>
      tab.classList.toggle('active', tab.dataset.tab === name)
    );
  }

  // --- 3) Клики по вкладках усередині модалки ---
  tabs.forEach(tab => {
    tab.addEventListener('click', e => {
      e.preventDefault();
      showTab(tab.dataset.tab);
    });
  });

  // --- 4) Клики на кнопки в header: відкривають модалку + потрібну вкладку ---
  headerLoginBtn.addEventListener('click', e => {
    e.preventDefault();
    showTab('login');
    modal.classList.add('show');
  });
  headerRegBtn.addEventListener('click', e => {
    e.preventDefault();
    showTab('register');
    modal.classList.add('show');
  });

  // --- 5) Закрити модалку ---
  closeBtn.addEventListener('click', () => {
    modal.classList.remove('show');
  });

  // --- 6) Загальний AJAX-submit для обох форм ---
  document.body.addEventListener('submit', async e => {
    const form = e.target;
    // ловимо тільки наші дві форми
    if (form.id !== 'login-form-ajax' && form.id !== 'register-form-ajax') return;

    e.preventDefault();
    const data = new FormData(form);
    const resp = await fetch(form.action, {
      method: 'POST',
      headers: {
        'X-CSRFToken': data.get('csrfmiddlewaretoken'),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: data
    });

    if (resp.ok) {
      // при успішному логіні/реєстрації – редірект
      const json = await resp.json();
      window.location.href = json.redirect_url;
    } else {
      // при помилці – вкидаємо назад HTML фрагмент форми
      const html = await resp.text();
      const targetBox = form.id === 'login-form-ajax'
        ? loginBox
        : registerBox;

      targetBox.innerHTML = html;
      // після заміни вмісту треба ще раз підвісити слухачі на вкладки,
      // або просто знову викликати showTab поточної вкладки:
      showTab(form.id === 'login-form-ajax' ? 'login' : 'register');
    }
  });
});
