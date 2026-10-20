/* ============================================================
   KAVITA CHEMIST — app.js  (load at the end of <body>)
   Every feature checks that its elements exist, so this file
   is safe on every page.
   ============================================================ */
(function () {
  'use strict';

  document.documentElement.classList.add('js');
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. Navbar: shadow on scroll + mobile menu ---------- */
  var navbar = $('.navbar');
  var navToggle = $('.nav-toggle');
  var navLinks = $('.nav-links');

  function setNav(open) {
    if (!navLinks || !navToggle) return;
    navLinks.classList.toggle('open', open);
    navToggle.setAttribute('aria-expanded', String(open));
  }
  if (navToggle && navLinks) {
    navToggle.setAttribute('aria-label', 'Toggle menu');
    navToggle.setAttribute('aria-expanded', 'false');
    navToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      setNav(!navLinks.classList.contains('open'));
    });
    $$('a', navLinks).forEach(function (a) { a.addEventListener('click', function () { setNav(false); }); });
    document.addEventListener('click', function (e) {
      if (!navLinks.contains(e.target) && !navToggle.contains(e.target)) setNav(false);
    });
    window.addEventListener('resize', function () { if (window.innerWidth > 768) setNav(false); });
  }

  /* ---------- 2. Highlight current page in nav/sidebar ---------- */
  ['.nav-link', '.sidebar-link'].forEach(function (sel) {
    var links = $$(sel);
    if (!links.length || links.some(function (l) { return l.classList.contains('active'); })) return;
    var path = location.pathname.replace(/\/+$/, '') || '/';
    links.forEach(function (l) {
      var href = l.getAttribute('href');
      if (!href || href.charAt(0) === '#') return;
      var p = href.split('?')[0].replace(/\/+$/, '') || '/';
      if (p === path) l.classList.add('active');
    });
  });

  /* ---------- 3. Dashboard sidebar (mobile) + overlay ---------- */
  var sidebar = $('.sidebar');
  var sbToggle = $('.sidebar-toggle');
  if (sidebar && sbToggle) {
    var overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);
    var setSidebar = function (open) {
      sidebar.classList.toggle('open', open);
      overlay.classList.toggle('show', open);
    };
    sbToggle.addEventListener('click', function () { setSidebar(!sidebar.classList.contains('open')); });
    overlay.addEventListener('click', function () { setSidebar(false); });
    $$('a', sidebar).forEach(function (a) { a.addEventListener('click', function () { setSidebar(false); }); });
    window.addEventListener('resize', function () { if (window.innerWidth > 768) setSidebar(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setSidebar(false); });
  }

  /* ---------- 4. Alerts: close button + auto-dismiss ---------- */
  function dismiss(alert) {
    alert.classList.add('hide');
    setTimeout(function () { if (alert.parentNode) alert.parentNode.removeChild(alert); }, 300);
  }
  $$('.alert').forEach(function (alert) {
    var close = $('.alert-close', alert);
    if (close) close.addEventListener('click', function () { dismiss(alert); });
    setTimeout(function () { dismiss(alert); }, 6000);
  });

  /* ---------- 5. Scroll reveal ---------- */
  var revealSel = '.feature-card, .testimonial-card, .team-card, .step, .stat-card, .feature-row, .about-grid > *, .cta-box, .contact-grid > *';
  var revealEls = $$(revealSel);
  if ('IntersectionObserver' in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in-view'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el, i) {
      el.classList.add('reveal');
      el.style.transitionDelay = (i % 4) * 70 + 'ms';
      io.observe(el);
    });
  }

  /* ---------- 6. Animated counters ---------- */
  function animateCount(el) {
    var raw = el.getAttribute('data-count') || el.textContent.trim();
    var m = raw.match(/^([^\d]*)([\d,]+(?:\.\d+)?)(.*)$/);
    if (!m) return;
    var target = parseFloat(m[2].replace(/,/g, ''));
    var decimals = (m[2].split('.')[1] || '').length;
    var start = null, dur = 1400;
    function tick(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      var val = (target * eased).toFixed(decimals);
      el.textContent = m[1] + Number(val).toLocaleString('en-IN', { minimumFractionDigits: decimals }) + m[3];
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  var counters = $$('[data-count], .hero-stat strong');
  if (counters.length && 'IntersectionObserver' in window && !reduceMotion) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { animateCount(en.target); cio.unobserve(en.target); }
      });
    }, { threshold: 0.6 });
    counters.forEach(function (c) { cio.observe(c); });
  }

  /* ---------- 7. Tables: responsive wrap, sort, live filter ---------- */
  $$('.data-table').forEach(function (table) {
    // wrap in a scroll container if the template forgot to
    if (!table.parentElement.classList.contains('table-wrapper')) {
      var wrap = document.createElement('div');
      wrap.className = 'table-wrapper';
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(table);
    }
    // click-to-sort on headers that have a title
    var headers = $$('thead th', table);
    var tbody = $('tbody', table);
    if (!tbody) return;
    headers.forEach(function (th, idx) {
      if (!th.textContent.trim() || /action/i.test(th.textContent)) return;
      th.classList.add('sortable');
      th.addEventListener('click', function () {
        var asc = !th.classList.contains('sort-asc');
        headers.forEach(function (h) { h.classList.remove('sort-asc', 'sort-desc'); });
        th.classList.add(asc ? 'sort-asc' : 'sort-desc');
        var rows = $$('tr:not(.no-results-row)', tbody);
        rows.sort(function (a, b) {
          var x = (a.cells[idx] ? a.cells[idx].textContent : '').trim();
          var y = (b.cells[idx] ? b.cells[idx].textContent : '').trim();
          var nx = parseFloat(x.replace(/[^\d.-]/g, '')), ny = parseFloat(y.replace(/[^\d.-]/g, ''));
          var cmp = (!isNaN(nx) && !isNaN(ny) && /\d/.test(x) && /\d/.test(y))
            ? nx - ny : x.localeCompare(y, undefined, { sensitivity: 'base' });
          return asc ? cmp : -cmp;
        });
        rows.forEach(function (r) { tbody.appendChild(r); });
      });
    });
  });

  // Opt-in instant filter:  <input data-filter-table="#myTable">
  $$('[data-filter-table]').forEach(function (input) {
    var table = $(input.getAttribute('data-filter-table'));
    if (!table) return;
    var tbody = $('tbody', table) || table;
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      $$('tr', tbody).forEach(function (row) {
        if (row.classList.contains('no-results-row')) return;
        var match = row.textContent.toLowerCase().indexOf(q) > -1;
        row.style.display = match ? '' : 'none';
        if (match) shown++;
      });
      var empty = $('.no-results-row', tbody);
      if (!shown && !empty) {
        var tr = document.createElement('tr');
        tr.className = 'no-results-row';
        tr.innerHTML = '<td colspan="99">No matching records</td>';
        tbody.appendChild(tr);
      } else if (shown && empty) { empty.remove(); }
    });
  });

  /* ---------- 8. Forms ---------- */
  // Password show/hide
  $$('input[type="password"]').forEach(function (input) {
    var wrap = document.createElement('span');
    wrap.className = 'pw-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'pw-toggle'; btn.textContent = 'Show';
    btn.setAttribute('aria-label', 'Show or hide password');
    btn.addEventListener('click', function () {
      var hidden = input.type === 'password';
      input.type = hidden ? 'text' : 'password';
      btn.textContent = hidden ? 'Hide' : 'Show';
    });
    wrap.appendChild(btn);
  });

  // Inline validation + loading state on submit
  $$('form').forEach(function (form) {
    $$('input, select, textarea', form).forEach(function (f) {
      f.addEventListener('blur', function () { f.classList.toggle('is-invalid', !f.checkValidity() && f.value !== ''); });
      f.addEventListener('input', function () { if (f.checkValidity()) f.classList.remove('is-invalid'); });
    });
    form.addEventListener('submit', function () {
      if (!form.checkValidity()) return;
      var btn = $('button[type="submit"], input[type="submit"]', form);
      if (btn && btn.tagName === 'BUTTON') {
        setTimeout(function () { btn.classList.add('is-loading'); btn.disabled = true; }, 0);
      }
    });
  });

  // Confirm dialogs:  <a href="..." data-confirm="Delete this medicine?">
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-confirm]');
    if (el && !window.confirm(el.getAttribute('data-confirm'))) e.preventDefault();
  });

  /* ---------- 9. Scroll: navbar shadow + back-to-top ---------- */
  var topBtn = document.createElement('button');
  topBtn.className = 'back-to-top';
  topBtn.type = 'button';
  topBtn.setAttribute('aria-label', 'Back to top');
  topBtn.innerHTML = '&uarr;';
  document.body.appendChild(topBtn);
  topBtn.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  });

  var ticking = false;
  function onScroll() {
    var y = window.scrollY || document.documentElement.scrollTop;
    if (navbar) navbar.classList.toggle('scrolled', y > 10);
    topBtn.classList.toggle('show', y > 500);
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  onScroll();
})();
