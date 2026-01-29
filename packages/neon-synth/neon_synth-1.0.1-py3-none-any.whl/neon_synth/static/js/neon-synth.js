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


  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function(link) {
      link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#') return;

        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          const headerHeight = document.querySelector('.synthwave-header')?.offsetHeight || 0;
          const targetPos = target.offsetTop - headerHeight - 20;

          window.scrollTo({
            top: targetPos,
            behavior: 'smooth'
          });

          history.pushState(null, null, href);
        }
      });
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
      const prefersReduced = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      try {
        window.scrollTo({ top: 0, behavior: prefersReduced ? 'auto' : 'smooth' });
      } catch (err) {
        window.scrollTo(0, 0);
      }
    });

    update();
  }


  function initPerformanceHint() {
    const hint = document.querySelector('.performance-hint');
    if (!hint) return;

    const actionButton = hint.querySelector('.performance-hint__action');
    const dismissButton = hint.querySelector('.performance-hint__dismiss');
    const effectsToggle = document.querySelector('.effects-toggle');

    if (!actionButton || !effectsToggle) return;

    let hasShown = false;
    let dismissed = false;
    let performanceAlert = false;
    let longTaskTime = 0;
    let longTaskCount = 0;
    let frames = 0;
    let slowFrames = 0;
    let totalDelta = 0;
    let monitorLabel = 'Monitoring';
    let observer = null;
    let hasLongTaskSupport = false;
    let rafLast = 0;
    let rafActive = false;
    let logTimer = null;

    const longTaskThreshold = 120;
    const slowThreshold = 24;
    const slowFramesThreshold = 15;
    const avgThreshold = 22;
    const maxFrames = 120;
    const logIntervalMs = 500;
    const slowRatioThreshold = slowFramesThreshold / maxFrames;

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

    function updateConsole(state, statusText) {
      setConsole(state, statusText, buildDetails());
    }

    updateConsole('monitor', monitorLabel);

    function setWarning(active) {
      effectsToggle.classList.toggle('is-warning', active);
    }

    function isEffectsLow() {
      return document.documentElement.getAttribute('data-effects') === 'low' ||
        document.body.getAttribute('data-effects') === 'low';
    }

    function updateWarning() {
      setWarning(performanceAlert && !isEffectsLow());
    }

    function isPerfLogEnabled() {
      const rootValue = document.documentElement.getAttribute('data-perf-log');
      const bodyValue = document.body ? document.body.getAttribute('data-perf-log') : null;
      return (bodyValue || rootValue) === 'on';
    }

    const perfLogEnabled = isPerfLogEnabled();

    function isPerfSoundEnabled() {
      const rootValue = document.documentElement.getAttribute('data-perf-sound');
      const bodyValue = document.body ? document.body.getAttribute('data-perf-sound') : null;
      return (bodyValue || rootValue) === 'on';
    }

    const perfSoundEnabled = isPerfSoundEnabled();
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    let audioContext = null;
    let pendingSiren = false;
    let sirenActive = false;
    let lastSirenAt = 0;
    const sirenCooldownMs = 5000;

    function ensureAudioContext() {
      if (!AudioContextClass) {
        return null;
      }
      if (!audioContext) {
        try {
          audioContext = new AudioContextClass();
        } catch (err) {
          audioContext = null;
        }
      }
      return audioContext;
    }

    function unlockAudioContext() {
      if (!perfSoundEnabled) {
        return;
      }
      const ctx = ensureAudioContext();
      if (!ctx) {
        return;
      }
      if (ctx.state === 'running') {
        if (pendingSiren) {
          pendingSiren = false;
          playSiren();
        }
        return;
      }
      if (ctx.state === 'suspended' && ctx.resume) {
        const resume = ctx.resume();
        if (resume && resume.then) {
          resume.then(function() {
            if (ctx.state === 'running' && pendingSiren) {
              pendingSiren = false;
              playSiren();
            }
          });
        }
      }
    }

    function setupAudioUnlock() {
      if (!perfSoundEnabled || !AudioContextClass) {
        return;
      }
      const unlockOnce = function() {
        unlockAudioContext();
      };
      window.addEventListener('pointerdown', unlockOnce, { once: true, passive: true });
      window.addEventListener('keydown', unlockOnce, { once: true });
    }

    function playSiren() {
      if (!perfSoundEnabled || isEffectsLow()) {
        return;
      }
      const nowMs = Date.now();
      if (sirenActive || (nowMs - lastSirenAt) < sirenCooldownMs) {
        return;
      }
      const ctx = ensureAudioContext();
      if (!ctx) {
        return;
      }
      if (ctx.state !== 'running') {
        pendingSiren = true;
        unlockAudioContext();
        return;
      }

      sirenActive = true;
      lastSirenAt = nowMs;

      const start = ctx.currentTime;
      const duration = 1.6;
      const carrier = ctx.createOscillator();
      const lfo = ctx.createOscillator();
      const lfoGain = ctx.createGain();
      const gain = ctx.createGain();

      carrier.type = 'sine';
      carrier.frequency.setValueAtTime(520, start);
      lfo.type = 'sine';
      lfo.frequency.setValueAtTime(2.2, start);
      lfoGain.gain.setValueAtTime(240, start);

      lfo.connect(lfoGain);
      lfoGain.connect(carrier.frequency);

      gain.gain.setValueAtTime(0.0001, start);
      gain.gain.exponentialRampToValueAtTime(0.08, start + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);

      carrier.connect(gain);
      gain.connect(ctx.destination);

      carrier.start(start);
      lfo.start(start);
      carrier.stop(start + duration + 0.05);
      lfo.stop(start + duration + 0.05);

      carrier.onended = function() {
        sirenActive = false;
      };
    }

    setupAudioUnlock();

    function isPerfNotifyEnabled() {
      const rootValue = document.documentElement.getAttribute('data-perf-notify');
      const bodyValue = document.body ? document.body.getAttribute('data-perf-notify') : null;
      return (bodyValue || rootValue) === 'on';
    }

    const perfNotifyEnabled = isPerfNotifyEnabled();
    let notificationAllowed = false;
    let notifyGeneralSent = false;
    let lastNotifyAt = 0;
    const notifyCooldownMs = 8000;

    function canNotify() {
      return perfNotifyEnabled && typeof Notification !== 'undefined';
    }

    function sendNotification(title, body, tag) {
      if (!canNotify() || !notificationAllowed) {
        return;
      }
      const nowMs = Date.now();
      if ((nowMs - lastNotifyAt) < notifyCooldownMs) {
        return;
      }
      try {
        new Notification(title, {
          body: body,
          tag: tag || 'neonbook-performance',
          renotify: false
        });
        lastNotifyAt = nowMs;
      } catch (err) {
      }
    }

    function requestNotificationPermission() {
      if (!canNotify()) {
        return;
      }
      if (Notification.permission === 'granted') {
        notificationAllowed = true;
        if (!notifyGeneralSent) {
          notifyGeneralSent = true;
          sendNotification('Neonbook', 'Notifications enabled. You will be warned if heavy load is detected.', 'neonbook-general');
        }
        return;
      }
      if (Notification.permission !== 'default') {
        return;
      }
      try {
        const request = Notification.requestPermission();
        if (request && request.then) {
          request.then(function(result) {
            if (result === 'granted') {
              notificationAllowed = true;
              if (!notifyGeneralSent) {
                notifyGeneralSent = true;
                sendNotification('Neonbook', 'Notifications enabled. You will be warned if heavy load is detected.', 'neonbook-general');
              }
            }
          });
        }
      } catch (err) {
      }
    }

    function setupNotificationRequest() {
      if (!canNotify()) {
        return;
      }
      const requestOnce = function() {
        requestNotificationPermission();
      };
      window.addEventListener('pointerdown', requestOnce, { once: true, passive: true });
      window.addEventListener('keydown', requestOnce, { once: true });
    }

    setupNotificationRequest();

    function hideHint() {
      hint.classList.remove('is-visible');
      hint.hidden = true;
      updateWarning();
    }

    function showHint() {
      const wasAlert = performanceAlert;
      performanceAlert = true;
      updateWarning();
      updateConsole('warn', 'Heavy render');
      if (!wasAlert) {
        playSiren();
        sendNotification('Neonbook', 'Heavy load detected. Consider turning off effects.', 'neonbook-heavy');
      }
      if (hasShown || dismissed || isEffectsLow()) return;
      hasShown = true;
      hint.hidden = false;
      hint.classList.add('is-visible');
    }

    actionButton.addEventListener('click', function() {
      effectsToggle.click();
      hideHint();
    });

    if (dismissButton) {
      dismissButton.addEventListener('click', function() {
        dismissed = true;
        hideHint();
      });
    }

    effectsToggle.addEventListener('click', function() {
      window.setTimeout(function() {
        if (isEffectsLow()) {
          hideHint();
        }
        updateWarning();
      }, 0);
    });

    updateWarning();

    function updateMonitorLabel() {
      monitorLabel = 'Monitoring';
    }

    function startRafLoop() {
      if (!window.requestAnimationFrame || rafActive) {
        return;
      }
      rafActive = true;
      updateMonitorLabel();
      updateConsole('monitor', monitorLabel);

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
      const effectsLabel = isEffectsLow() ? 'Low' : 'Full';
      const frameLabel = frames ? slowFrames + ' of ' + frames : 'no frame data';
      console.log('[Neonbook Performance] ' + statusText + '. Monitoring average frame time, ' +
        'slow frames, and long tasks. Avg frame time: ' +
        (frames ? avg.toFixed(1) : 'n/a') + 'ms; slow frames: ' + frameLabel +
        '; long tasks: ' + longLabel + '. Effects: ' + effectsLabel + '.');
    }

    function evaluateAndLog() {
      const avg = frames ? totalDelta / frames : 0;
      const slowRatio = frames ? slowFrames / frames : 0;
      const heavy = longTaskTime >= longTaskThreshold ||
        (frames && (avg >= avgThreshold || slowRatio >= slowRatioThreshold));
      if (heavy) {
        showHint();
      }
      const warningActive = performanceAlert && !isEffectsLow();
      const statusText = warningActive ? 'Heavy render' : (frames || longTaskCount ? 'OK' : 'Monitoring');
      const state = warningActive ? 'warn' : (frames || longTaskCount ? 'ok' : 'monitor');
      updateMonitorLabel();
      updateConsole(state, statusText);
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
          observer = new PerformanceObserver(function(list) {
            list.getEntries().forEach(function(entry) {
              longTaskTime += entry.duration;
              longTaskCount += 1;
            });
            if (!performanceAlert) {
              updateConsole('monitor', monitorLabel);
            }
            if (longTaskTime >= longTaskThreshold) {
              showHint();
            }
          });
          observer.observe({ entryTypes: ['longtask'] });
        }
      } catch (err) {
        observer = null;
        hasLongTaskSupport = false;
      }
    }

    updateMonitorLabel();
    if (window.requestAnimationFrame) {
      startRafLoop();
    } else if (hasLongTaskSupport) {
      updateConsole('monitor', monitorLabel);
    } else {
      updateConsole('ok', 'No monitor');
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
    initSmoothScroll();
    initBackToTop();
    initPerformanceHint();
    initKeyboardNav();
    initCurrentPage();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
