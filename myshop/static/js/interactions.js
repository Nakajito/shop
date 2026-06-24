/* ============================================================
   SYNK FOOD — Site-wide Interactions
   ============================================================ */

(function () {
  'use strict';

  /* ── 1. Page load fade-in ────────────────────────────────── */
  document.documentElement.classList.add('sk-loaded');

  /* ── 2. Navbar: scroll shrink + hide/show ────────────────── */
  const nav = document.querySelector('.sf-nav');
  if (nav) {
    let lastY = 0;
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      nav.classList.toggle('sf-nav--scrolled', y > 40);
      nav.classList.toggle('sf-nav--hidden', y > lastY && y > 120);
      lastY = y;
    }, { passive: true });
  }

  /* ── 3. Dropdown de usuario ──────────────────────────────── */
  const userWrap = document.getElementById('sfUserWrap');
  const userBtn  = document.getElementById('sfUserBtn');
  if (userWrap && userBtn) {
    userBtn.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = userWrap.classList.toggle('open');
      userBtn.setAttribute('aria-expanded', isOpen);
    });
    document.addEventListener('click', e => {
      if (!userWrap.contains(e.target)) {
        userWrap.classList.remove('open');
        userBtn.setAttribute('aria-expanded', 'false');
      }
    });
    // Cerrar con Escape
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        userWrap.classList.remove('open');
        userBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ── 4. Mobile nav drawer ────────────────────────────────── */
  const navToggle  = document.getElementById('sfNavToggle');
  const navDrawer  = document.getElementById('sfNavDrawer');
  const navOverlay = document.getElementById('sfNavOverlay');
  const navClose   = document.getElementById('sfNavClose');

  function openDrawer() {
    navDrawer?.classList.add('sf-nav__drawer--open');
    navOverlay?.classList.add('sf-nav__overlay--visible');
    navToggle?.classList.add('sf-nav__toggle--open');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    navDrawer?.classList.remove('sf-nav__drawer--open');
    navOverlay?.classList.remove('sf-nav__overlay--visible');
    navToggle?.classList.remove('sf-nav__toggle--open');
    document.body.style.overflow = '';
  }

  if (navToggle)  navToggle.addEventListener('click', openDrawer);
  if (navClose)   navClose.addEventListener('click', closeDrawer);
  if (navOverlay) navOverlay.addEventListener('click', closeDrawer);
  navDrawer?.querySelectorAll('a').forEach(a => a.addEventListener('click', closeDrawer));
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });

  /* ── 5. Scroll reveal ────────────────────────────────────── */
  const revealEls = document.querySelectorAll(
    '.ct-row, .ct-summary, .pd-info, .pd-gallery, ' +
    '.sf-testimonios__card, .sf-prod-card, .os-marcas__card, ' +
    '.ct-rec-card, .pd-rec-card, .sk-sidebar, .card'
  );

  if ('IntersectionObserver' in window && revealEls.length) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('sk-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealEls.forEach((el, i) => {
      el.classList.add('sk-reveal');
      el.style.transitionDelay = `${(i % 4) * 60}ms`;
      io.observe(el);
    });
  }

  /* ── 6. Toast notification ───────────────────────────────── */
  window.skToast = function (msg, type = 'success') {
    let container = document.getElementById('sk-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'sk-toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `sk-toast sk-toast--${type}`;
    toast.innerHTML = `
      <span class="sk-toast__icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
      <span>${msg}</span>
    `;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('sk-toast--show'));
    setTimeout(() => {
      toast.classList.remove('sk-toast--show');
      setTimeout(() => toast.remove(), 350);
    }, 3000);
  };

  /* ── 7. Add to cart: AJAX (product detail) ─────────────── */
  document.querySelectorAll('form[data-ajax-add]').forEach(form => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn = this.querySelector('.pd-btn--add, .add-cart-btn');
      const body = new URLSearchParams(new FormData(this));
      fetch(this.getAttribute('action'), {
        method: 'POST',
        headers: {
          'X-CSRFToken': skGetCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body.toString(),
      })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data || !data.ok) {
          if (window.skToast) window.skToast('No se pudo agregar el producto', 'error');
          return;
        }
        if (window.skToast) window.skToast('Producto agregado al carrito');
        skUpdateCartBadge(data.cart_len);
        if (btn) {
          const original = btn.innerHTML;
          btn.innerHTML = '✓ Agregado';
          btn.style.background = '#2e7d32';
          setTimeout(() => {
            btn.innerHTML = original;
            btn.style.background = '';
          }, 1800);
        }
      })
      .catch(() => {
        if (window.skToast) window.skToast('No se pudo agregar el producto', 'error');
      });
    });
  });

  /* ── 8. Smooth scroll para anchors ──────────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ── 9. Image lazy hover zoom (product list) ─────────────── */
  document.querySelectorAll('.sf-prod-card__img, .pd-rec-card__img, .ct-rec-card__img').forEach(img => {
    img.closest('a, div')?.addEventListener('mouseenter', () => {
      img.style.transform = 'scale(1.06)';
    });
    img.closest('a, div')?.addEventListener('mouseleave', () => {
      img.style.transform = '';
    });
  });

  /* ── 10. Alert auto-dismiss ──────────────────────────────── */
  document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 4500);
  });

  /* ── 11. Ripple en botones ───────────────────────────────── */
  document.querySelectorAll('.ct-checkout-btn, .pd-btn--add, .sf-btn--dark, .ct-coupon__btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const rect   = this.getBoundingClientRect();
      const ripple = document.createElement('span');
      ripple.className = 'sk-ripple';
      ripple.style.left   = `${e.clientX - rect.left}px`;
      ripple.style.top    = `${e.clientY - rect.top}px`;
      this.style.position = 'relative';
      this.style.overflow = 'hidden';
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });

  /* ── 12. Número del carrito animado ─────────────────────── */
  const badge = document.querySelector('.sf-nav__cart-badge');
  if (badge) {
    badge.style.animation = 'sk-badge-pop 0.4s cubic-bezier(0.34,1.56,0.64,1) both';
  }

  /* ── 13. Catálogo: favorito + agregar al carrito (AJAX) ──── */
  function skGetCookie(name) {
    let v = null;
    if (document.cookie) {
      document.cookie.split(';').forEach(c => {
        c = c.trim();
        if (c.startsWith(name + '=')) v = decodeURIComponent(c.slice(name.length + 1));
      });
    }
    return v;
  }

  function skUpdateCartBadge(count) {
    let b = document.querySelector('.sf-nav__cart-badge');
    if (count > 0) {
      if (!b) {
        const cartLink = document.querySelector('.sf-nav__cart');
        if (cartLink) {
          b = document.createElement('span');
          b.className = 'sf-nav__cart-badge';
          cartLink.appendChild(b);
        }
      }
      if (b) {
        b.textContent = count;
        b.style.animation = 'none';
        // force reflow to restart animation
        void b.offsetWidth;
        b.style.animation = 'sk-badge-pop 0.4s cubic-bezier(0.34,1.56,0.64,1) both';
      }
    } else if (b) {
      b.remove();
    }
  }

  /* Agregar al carrito */
  document.querySelectorAll('.js-add-cart-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const body = new URLSearchParams();
      body.append('quantity', '1');
      body.append('override', 'false');
      fetch(this.dataset.url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': skGetCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body.toString(),
      })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data || !data.ok) {
          if (window.skToast) window.skToast('No se pudo agregar el producto', 'error');
          return;
        }
        if (window.skToast) window.skToast('Producto agregado al carrito');
        skUpdateCartBadge(data.cart_len);
        this.classList.add('is-added');
        setTimeout(() => {
          this.classList.remove('is-added');
        }, 1800);
      })
      .catch(() => {
        if (window.skToast) window.skToast('No se pudo agregar el producto', 'error');
      });
    });
  });

  /* Favorito */
  document.querySelectorAll('.js-fav-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      fetch(this.dataset.url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': skGetCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest',
        },
      })
      .then(r => {
        // login_required redirects (302) unauthenticated users to the login page;
        // fetch follows it, so detect the redirect / non-JSON response.
        if (r.status === 401 || r.status === 403 || r.redirected ||
            !(r.headers.get('content-type') || '').includes('application/json')) {
          window.location.href = this.dataset.loginUrl || '/accounts/login/';
          return null;
        }
        return r.json();
      })
      .then(data => {
        if (!data) return;
        const svg = this.querySelector('.prod-fav-icon');
        if (data.is_favorite) {
          this.classList.add('is-active');
          if (svg) svg.setAttribute('fill', 'currentColor');
          if (window.skToast) window.skToast('Agregado a favoritos');
        } else {
          this.classList.remove('is-active');
          if (svg) svg.setAttribute('fill', 'none');
          if (window.skToast) window.skToast('Eliminado de favoritos', 'info');
        }
      })
      .catch(() => {});
    });
  });

})();

/* ── Search Overlay (shared navbar) ── */
(function() {
  const sfSearchToggle  = document.getElementById('sfSearchToggle');
  const sfSearchOverlay = document.getElementById('sfSearchOverlay');
  const sfSearchClose   = document.getElementById('sfSearchClose');

  if (!sfSearchToggle || !sfSearchOverlay) return;

  const sfSearchInput = sfSearchOverlay.querySelector('.sf-search-input');

  sfSearchToggle.addEventListener('click', () => {
    sfSearchOverlay.classList.add('sf-search-overlay--open');
    sfSearchInput && sfSearchInput.focus();
  });
  sfSearchClose.addEventListener('click', () => {
    sfSearchOverlay.classList.remove('sf-search-overlay--open');
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') sfSearchOverlay.classList.remove('sf-search-overlay--open');
  });
})();
