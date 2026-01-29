(function() {
  'use strict';

  const THEME_STORAGE_KEY = 'neonbook-theme';
  const LEGACY_THEME_KEYS = ['neon-wave'];
  const EFFECTS_STORAGE_KEY = 'neonbook-effects';
  const THEMES = ['dark', 'light', 'system'];
  const EFFECTS = ['full', 'low'];
  const NAME_STORAGE_PREFIX = 'neonbook:';
  const preferNameStore = window.location && window.location.protocol === 'file:';

  function safeGet(storage, key) {
    if (!storage) return null;
    try {
      return storage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function safeSet(storage, key, value) {
    if (!storage) return false;
    try {
      storage.setItem(key, value);
      return true;
    } catch (e) {
      return false;
    }
  }

  function readNameStore() {
    if (!window.name || window.name.indexOf(NAME_STORAGE_PREFIX) !== 0) {
      return null;
    }
    const raw = window.name.slice(NAME_STORAGE_PREFIX.length);
    try {
      return JSON.parse(raw) || {};
    } catch (e) {
      return null;
    }
  }

  function writeNameStore(store, force) {
    if (!force && window.name && window.name.indexOf(NAME_STORAGE_PREFIX) !== 0) {
      return false;
    }
    try {
      window.name = NAME_STORAGE_PREFIX + JSON.stringify(store || {});
      return true;
    } catch (e) {
      return false;
    }
  }

  function getNameValue(key) {
    const store = readNameStore();
    if (store && Object.prototype.hasOwnProperty.call(store, key)) {
      return store[key];
    }
    return null;
  }

  function setNameValue(key, value, force) {
    const store = readNameStore() || {};
    store[key] = value;
    writeNameStore(store, force);
  }


  function getSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  }


  function getEffectiveTheme(theme) {
    return theme === 'system' ? getSystemTheme() : theme;
  }


  function getStoredTheme() {
    if (preferNameStore) {
      const nameValue = getNameValue(THEME_STORAGE_KEY);
      if (nameValue && THEMES.includes(nameValue)) {
        return nameValue;
      }
      for (const key of LEGACY_THEME_KEYS) {
        const legacyName = getNameValue(key);
        if (legacyName && THEMES.includes(legacyName)) {
          return legacyName;
        }
      }
    }
    const stored = safeGet(localStorage, THEME_STORAGE_KEY);
    if (stored && THEMES.includes(stored)) {
      return stored;
    }
    for (const key of LEGACY_THEME_KEYS) {
      const legacy = safeGet(localStorage, key);
      if (legacy && THEMES.includes(legacy)) {
        return legacy;
      }
    }
    if (!preferNameStore) {
      const nameValue = getNameValue(THEME_STORAGE_KEY);
      if (nameValue && THEMES.includes(nameValue)) {
        return nameValue;
      }
      for (const key of LEGACY_THEME_KEYS) {
        const legacyName = getNameValue(key);
        if (legacyName && THEMES.includes(legacyName)) {
          return legacyName;
        }
      }
    }
    return 'system';
  }


  function setStoredTheme(theme) {
    safeSet(localStorage, THEME_STORAGE_KEY, theme);
    setNameValue(THEME_STORAGE_KEY, theme, preferNameStore);
  }


  function applyTheme(theme) {
    const effective = getEffectiveTheme(theme);
    document.documentElement.setAttribute('data-theme', effective);
    document.documentElement.setAttribute('data-theme-setting', theme);

    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      const bg = getComputedStyle(document.documentElement).getPropertyValue('--bg-deep').trim();
      if (bg) {
        metaThemeColor.setAttribute('content', bg);
      }
    }
  }


  function cycleTheme() {
    const current = getStoredTheme();
    const currentIndex = THEMES.indexOf(current);
    const nextIndex = (currentIndex + 1) % THEMES.length;
    const nextTheme = THEMES[nextIndex];

    setStoredTheme(nextTheme);
    applyTheme(nextTheme);

    return nextTheme;
  }


  function initToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', function() {
      const newTheme = cycleTheme();

      const titles = {
        dark: 'Current: Dark theme. Click for Light.',
        light: 'Current: Light theme. Click for System.',
        system: 'Current: System theme. Click for Dark.'
      };
      toggle.setAttribute('title', titles[newTheme] || 'Toggle theme');
    });

    const current = getStoredTheme();
    const titles = {
      dark: 'Current: Dark theme. Click for Light.',
      light: 'Current: Light theme. Click for System.',
      system: 'Current: System theme. Click for Dark.'
    };
    toggle.setAttribute('title', titles[current] || 'Toggle theme');
  }


  function watchSystemTheme() {
    if (!window.matchMedia) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = function() {
      if (getStoredTheme() === 'system') {
        applyTheme('system');
      }
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(handler);
    }
  }


  function getStoredEffects() {
    if (preferNameStore) {
      const nameValue = getNameValue(EFFECTS_STORAGE_KEY);
      if (nameValue && EFFECTS.includes(nameValue)) {
        return nameValue;
      }
    }
    const stored = safeGet(localStorage, EFFECTS_STORAGE_KEY);
    if (stored && EFFECTS.includes(stored)) {
      return stored;
    }
    if (!preferNameStore) {
      const nameValue = getNameValue(EFFECTS_STORAGE_KEY);
      if (nameValue && EFFECTS.includes(nameValue)) {
        return nameValue;
      }
    }
    const rootFallback = document.documentElement.getAttribute('data-effects');
    if (rootFallback && EFFECTS.includes(rootFallback)) {
      return rootFallback;
    }
    const bodyFallback = document.body ? document.body.getAttribute('data-effects') : null;
    if (bodyFallback && EFFECTS.includes(bodyFallback)) {
      return bodyFallback;
    }
    return 'full';
  }


  function setStoredEffects(mode) {
    safeSet(localStorage, EFFECTS_STORAGE_KEY, mode);
    setNameValue(EFFECTS_STORAGE_KEY, mode, preferNameStore);
  }


  function applyEffects(mode) {
    const value = mode === 'low' ? 'low' : 'full';
    document.documentElement.setAttribute('data-effects', value);
    if (document.body) {
      document.body.setAttribute('data-effects', value);
    }
  }


  function toggleEffects() {
    const current = getStoredEffects();
    const next = current === 'low' ? 'full' : 'low';
    setStoredEffects(next);
    applyEffects(next);
    return next;
  }


  function initEffectsToggle() {
    const toggle = document.getElementById('effects-toggle');
    if (!toggle) return;

    function updateLabel(mode) {
      const isLow = mode === 'low';
      toggle.setAttribute('aria-pressed', isLow ? 'true' : 'false');
      toggle.setAttribute('data-state', mode);
      toggle.setAttribute('title', isLow ? 'Effects: Low. Click for Full.' : 'Effects: Full. Click for Low.');
    }

    toggle.addEventListener('click', function() {
      updateLabel(toggleEffects());
    });

    updateLabel(getStoredEffects());
  }

  (function() {
    applyTheme(getStoredTheme());
    applyEffects(getStoredEffects());
  })();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initToggle();
      watchSystemTheme();
      initEffectsToggle();
      applyEffects(getStoredEffects());
    });
  } else {
    initToggle();
    watchSystemTheme();
    initEffectsToggle();
    applyEffects(getStoredEffects());
  }

})();
