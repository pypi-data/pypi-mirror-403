(function() {
  'use strict';

  function initSidebar() {
    const toggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.synthwave-sidebar');

    if (!toggle || !sidebar) return;

    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    function openSidebar() {
      sidebar.classList.add('open');
      overlay.classList.add('active');
      toggle.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
      sidebar.classList.remove('open');
      overlay.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }

    toggle.addEventListener('click', function() {
      if (sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    overlay.addEventListener('click', closeSidebar);

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && sidebar.classList.contains('open')) {
        closeSidebar();
      }
    });

    sidebar.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        if (window.innerWidth < 768) {
          closeSidebar();
        }
      });
    });
  }

  function initTocHighlight() {
    const toc = document.querySelector('.synthwave-toc');
    if (!toc) return;

    const links = toc.querySelectorAll('a');
    const headings = [];

    links.forEach(function(link) {
      const href = link.getAttribute('href');
      if (href && href.startsWith('#')) {
        const id = href.slice(1);
        const heading = document.getElementById(id);
        if (heading) {
          headings.push({ link: link, heading: heading });
        }
      }
    });

    if (headings.length === 0) return;

    function updateHighlight() {
      const scrollPos = window.scrollY + 100;

      let current = null;
      for (let i = headings.length - 1; i >= 0; i--) {
        if (headings[i].heading.offsetTop <= scrollPos) {
          current = headings[i];
          break;
        }
      }

      links.forEach(function(link) {
        link.classList.remove('active');
      });

      if (current) {
        current.link.classList.add('active');
      }
    }

    let ticking = false;
    window.addEventListener('scroll', function() {
      if (!ticking) {
        requestAnimationFrame(function() {
          updateHighlight();
          ticking = false;
        });
        ticking = true;
      }
    });

    updateHighlight();
  }

  function initCodeBlocks() {
    document.querySelectorAll('div.highlight').forEach(function(block) {
      const classes = block.className.split(' ');
      for (let i = 0; i < classes.length; i++) {
        const cls = classes[i];
        if (cls.startsWith('highlight-') && cls !== 'highlight') {
          const lang = cls.replace('highlight-', '');
          if (lang && lang !== 'default') {
            block.setAttribute('data-lang', lang);
          }
          break;
        }
      }
    });
  }

  function initBackToTop() {
    const button = document.querySelector('.back-to-top');
    if (!button) return;

    function setVisible(visible) {
      button.hidden = !visible;
      button.classList.toggle('is-visible', visible);
      button.setAttribute('aria-hidden', visible ? 'false' : 'true');
    }

    function update() {
      setVisible(window.scrollY > 100);
    }

    let ticking = false;
    window.addEventListener('scroll', function() {
      if (!ticking) {
        requestAnimationFrame(function() {
          update();
          ticking = false;
        });
        ticking = true;
      }
    });

    button.addEventListener('click', function() {
      window.scrollTo(0, 0);
    });

    update();
  }

  function initPerformanceMonitor() {
    const rootValue = document.documentElement.getAttribute('data-perf-log');
    const bodyValue = document.body ? document.body.getAttribute('data-perf-log') : null;
    const perfLogEnabled = (bodyValue || rootValue) === 'on';

    let frames = 0;
    let slowFrames = 0;
    let totalDelta = 0;
    let longTaskTime = 0;
    let longTaskCount = 0;
    let hasLongTaskSupport = false;
    let rafLast = 0;
    let rafActive = false;
    let logTimer = null;

    const slowThreshold = 24;
    const logIntervalMs = 500;

    function createPerformanceConsole() {
      let container = document.querySelector('.performance-console');
      if (!container) {
        container = document.createElement('div');
        container.className = 'performance-console';
        container.innerHTML =
          '<div class="performance-console__title">Performance</div>' +
          '<div class="performance-console__status"></div>' +
          '<div class="performance-console__details"></div>';
        document.body.appendChild(container);
      }

      return {
        container: container,
        statusEl: container.querySelector('.performance-console__status'),
        detailsEl: container.querySelector('.performance-console__details')
      };
    }

    const perfConsole = createPerformanceConsole();

    function buildDetails() {
      const avg = frames ? totalDelta / frames : 0;
      const longLabel = hasLongTaskSupport
        ? longTaskCount + ' (' + Math.round(longTaskTime) + 'ms)'
        : 'unavailable';
      if (!frames && !longTaskCount) {
        return 'Avg -- | Slow -- | Long --';
      }
      return 'Avg ' + avg.toFixed(1) + 'ms | Slow ' + slowFrames + '/' + frames +
        ' | Long ' + longLabel;
    }

    function setConsole(state, statusText, detailsText) {
      if (!perfConsole || !perfConsole.container) return;
      perfConsole.container.setAttribute('data-state', state);
      if (perfConsole.statusEl) {
        perfConsole.statusEl.textContent = statusText;
      }
      if (perfConsole.detailsEl) {
        perfConsole.detailsEl.textContent = detailsText || '';
      }
    }

    function updateConsole(statusText) {
      const state = (frames || longTaskCount) ? 'ok' : 'monitor';
      setConsole(state, statusText, buildDetails());
    }

    function startRafLoop() {
      if (!window.requestAnimationFrame || rafActive) {
        return;
      }
      rafActive = true;
      updateConsole('Monitoring');

      function raf(now) {
        if (!rafActive) {
          return;
        }
        const current = now || Date.now();
        if (rafLast) {
          const delta = current - rafLast;
          if (delta < 200) {
            frames += 1;
            totalDelta += delta;
            if (delta > slowThreshold) {
              slowFrames += 1;
            }
          }
        }
        rafLast = current;
        window.requestAnimationFrame(raf);
      }

      window.requestAnimationFrame(raf);
    }

    function logPerformance(statusText) {
      if (!perfLogEnabled || !window.console || !console.log) {
        return;
      }
      const avg = frames ? totalDelta / frames : 0;
      const longLabel = hasLongTaskSupport
        ? longTaskCount + ' (' + Math.round(longTaskTime) + 'ms)'
        : 'unavailable';
      const frameLabel = frames ? slowFrames + ' of ' + frames : 'no frame data';
      console.log('[Neonbook Performance] ' + statusText + '. Monitoring average frame time, ' +
        'slow frames, and long tasks. Avg frame time: ' +
        (frames ? avg.toFixed(1) : 'n/a') + 'ms; slow frames: ' + frameLabel +
        '; long tasks: ' + longLabel + '.');
    }

    function evaluateAndLog() {
      const statusText = (frames || longTaskCount) ? 'Active' : 'Monitoring';
      updateConsole(statusText);
      logPerformance(statusText);
      frames = 0;
      slowFrames = 0;
      totalDelta = 0;
      longTaskTime = 0;
      longTaskCount = 0;
    }

    function startLogging() {
      if (logTimer) {
        clearInterval(logTimer);
      }
      logTimer = window.setInterval(evaluateAndLog, logIntervalMs);
    }

    if ('PerformanceObserver' in window) {
      try {
        const supported = PerformanceObserver.supportedEntryTypes || [];
        if (supported.indexOf('longtask') !== -1) {
          hasLongTaskSupport = true;
          const observer = new PerformanceObserver(function(list) {
            list.getEntries().forEach(function(entry) {
              longTaskTime += entry.duration;
              longTaskCount += 1;
            });
            updateConsole(frames || longTaskCount ? 'Active' : 'Monitoring');
          });
          observer.observe({ entryTypes: ['longtask'] });
        }
      } catch (err) {
        hasLongTaskSupport = false;
      }
    }

    if (window.requestAnimationFrame) {
      startRafLoop();
    } else if (hasLongTaskSupport) {
      updateConsole('Monitoring');
    } else {
      setConsole('ok', 'No monitor', buildDetails());
    }
    startLogging();
  }

  function initKeyboardNav() {
    document.addEventListener('keydown', function(e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      if (e.key === 'ArrowLeft' && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
        const prev = document.querySelector('.nav-prev');
        if (prev) {
          prev.click();
        }
      }

      if (e.key === 'ArrowRight' && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
        const next = document.querySelector('.nav-next');
        if (next) {
          next.click();
        }
      }

      if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
        const search = document.querySelector('input[type="search"], input[name="q"]');
        if (search) {
          e.preventDefault();
          search.focus();
        }
      }
    });
  }

  function initCurrentPage() {
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');

    sidebarLinks.forEach(function(link) {
      const linkPath = new URL(link.href).pathname;
      if (linkPath === currentPath) {
        link.classList.add('current');
      }
    });
  }

  function init() {
    initSidebar();
    initTocHighlight();
    initCodeBlocks();
    initBackToTop();
    initPerformanceMonitor();
    initKeyboardNav();
    initCurrentPage();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
