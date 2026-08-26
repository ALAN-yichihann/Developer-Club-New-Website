(function () {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  root.dataset.theme = savedTheme || (prefersDark ? 'dark' : 'light');

  const themeToggle = document.querySelector('[data-theme-toggle]');
  const menuToggle = document.querySelector('[data-menu-toggle]');
  const navLinks = document.querySelector('[data-nav-links]');
  const header = document.querySelector('[data-site-header]');
  const backToTop = document.querySelector('[data-back-to-top]');

  function updateThemeLabel() {
    if (!themeToggle) {
      return;
    }
    const isDark = root.dataset.theme === 'dark';
    themeToggle.textContent = isDark ? '☀' : '◐';
    themeToggle.setAttribute('aria-label', isDark ? '切换为浅色主题' : '切换为深色主题');
  }

  updateThemeLabel();

  themeToggle?.addEventListener('click', function () {
    const nextTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = nextTheme;
    localStorage.setItem('theme', nextTheme);
    updateThemeLabel();
  });

  menuToggle?.addEventListener('click', function () {
    const isOpen = menuToggle.getAttribute('aria-expanded') === 'true';
    menuToggle.setAttribute('aria-expanded', String(!isOpen));
    navLinks?.classList.toggle('is-open', !isOpen);
  });

  navLinks?.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      menuToggle?.setAttribute('aria-expanded', 'false');
      navLinks.classList.remove('is-open');
    });
  });

  function updateScrollState() {
    const hasScrolled = window.scrollY > 24;
    header?.classList.toggle('is-scrolled', hasScrolled);
    backToTop?.classList.toggle('is-visible', window.scrollY > 500);
  }

  window.addEventListener('scroll', updateScrollState, { passive: true });
  updateScrollState();

  backToTop?.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  const revealElements = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealElements.length) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });

    revealElements.forEach(function (element) {
      observer.observe(element);
    });
  } else {
    revealElements.forEach(function (element) {
      element.classList.add('is-visible');
    });
  }
}());
