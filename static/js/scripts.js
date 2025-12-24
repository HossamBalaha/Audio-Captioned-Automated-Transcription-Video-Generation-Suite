/**
 * T2V Suite - Main JavaScript Module
 * Handles form validation, API interactions, UI feedback, and user experience
 */

// ============================================
// Toast Notification System
// ============================================

class ToastNotification {
  constructor() {
    this.container = null;
    this.initContainer();
  }

  initContainer() {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    this.container = container;
  }

  show(title, message, type = 'info', duration = 5000) {
    const toastId = `toast-${Date.now()}`;

    const iconMap = {
      'success': 'bi-check-circle',
      'error': 'bi-exclamation-circle',
      'warning': 'bi-exclamation-triangle',
      'info': 'bi-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.id = toastId;
    toast.innerHTML = `
            <div class="toast-icon">
                <i class="bi ${iconMap[type] || iconMap['info']}" aria-hidden="true"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <p class="toast-message">${message}</p>
            </div>
            <button class="toast-close" aria-label="Close notification" data-toast-id="${toastId}">
                <i class="bi bi-x" aria-hidden="true"></i>
            </button>
        `;

    this.container.appendChild(toast);

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => this.remove(toastId));

    if (duration > 0) {
      setTimeout(() => this.remove(toastId), duration);
    }

    return toastId;
  }

  remove(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
      toast.remove();
    }
  }

  success(title, message) {
    return this.show(title, message, 'success', 5000);
  }

  error(title, message) {
    return this.show(title, message, 'error', 6000);
  }

  warning(title, message) {
    return this.show(title, message, 'warning', 5000);
  }

  info(title, message) {
    return this.show(title, message, 'info', 4000);
  }
}

// ============================================
// Form Validation & Field Management
// ============================================

class FormValidator {
  constructor(formSelector) {
    this.form = document.querySelector(formSelector);
    this.errors = {};
    this.touchedFields = new Set();
    if (this.form) {
      this.attachListeners();
    }
  }

  attachListeners() {
    this.form.addEventListener('blur', (e) => this.handleFieldBlur(e), true);
    this.form.addEventListener('change', (e) => this.handleFieldChange(e), true);
    this.form.addEventListener('input', (e) => this.handleFieldInput(e), true);
  }

  handleFieldBlur(e) {
    if (e.target.name) {
      this.touchedFields.add(e.target.name);
      this.validateField(e.target);
    }
  }

  handleFieldChange(e) {
    if (e.target.name && this.touchedFields.has(e.target.name)) {
      this.validateField(e.target);
    }
  }

  handleFieldInput(e) {
    if (e.target.name && this.touchedFields.has(e.target.name)) {
      this.validateField(e.target);
    }
  }

  validateField(field) {
    const fieldName = field.name;
    let isValid = true;
    let errorMsg = '';

    if (field.hasAttribute('required') && !field.value.trim()) {
      isValid = false;
      errorMsg = 'This field is required';
    } else if (field.type === 'email' && field.value && !this.isValidEmail(field.value)) {
      isValid = false;
      errorMsg = 'Please enter a valid email address';
    } else if (field.type === 'number' && field.value) {
      if (field.min && Number(field.value) < Number(field.min)) {
        isValid = false;
        errorMsg = `Value must be at least ${field.min}`;
      }
      if (field.max && Number(field.value) > Number(field.max)) {
        isValid = false;
        errorMsg = `Value must be at most ${field.max}`;
      }
    } else if (field.hasAttribute('minlength') && field.value.length < field.minlength) {
      isValid = false;
      errorMsg = `Minimum ${field.minlength} characters required`;
    }

    this.setFieldState(field, isValid, errorMsg);
    return isValid;
  }

  setFieldState(field, isValid, errorMsg = '') {
    if (isValid) {
      field.classList.remove('field-error', 'is-invalid');
      field.classList.add('field-success', 'is-valid');
      this.removeFieldError(field.name);
    } else {
      field.classList.remove('field-success', 'is-valid');
      field.classList.add('field-error', 'is-invalid');
      this.setFieldError(field.name, errorMsg);
    }
  }

  setFieldError(fieldName, message) {
    this.errors[fieldName] = message;
    this.displayFieldError(fieldName, message);
  }

  removeFieldError(fieldName) {
    delete this.errors[fieldName];
    this.removeFieldErrorDisplay(fieldName);
  }

  displayFieldError(fieldName, message) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    if (!field) return;

    let errorElement = field.parentElement.querySelector('.field-error-message');
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.className = 'field-error-message';
      field.parentElement.appendChild(errorElement);
    }
    errorElement.textContent = message;
  }

  removeFieldErrorDisplay(fieldName) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    if (!field) return;

    const errorElement = field.parentElement.querySelector('.field-error-message');
    if (errorElement) {
      errorElement.remove();
    }
  }

  isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  validateAll() {
    if (!this.form) return true;

    const fields = this.form.querySelectorAll('[required], [minlength], [type="email"], [type="number"]');
    let isFormValid = true;

    fields.forEach(field => {
      this.touchedFields.add(field.name);
      if (!this.validateField(field)) {
        isFormValid = false;
      }
    });

    return isFormValid;
  }

  getErrors() {
    return this.errors;
  }

  reset() {
    this.errors = {};
    this.touchedFields.clear();
    if (this.form) {
      this.form.querySelectorAll('.field-error-message').forEach(el => el.remove());
      this.form.querySelectorAll('input, select, textarea').forEach(field => {
        field.classList.remove('field-error', 'field-success', 'is-invalid', 'is-valid');
      });
    }
  }
}

// ============================================
// Character Counter
// ============================================

class CharacterCounter {
  constructor(textareaSelector, counterId, minChars = 0, maxChars = 5000) {
    this.textarea = document.querySelector(textareaSelector);
    this.counter = document.querySelector(counterId);
    this.minChars = minChars;
    this.maxChars = maxChars;

    if (this.textarea) {
      this.init();
    }
  }

  init() {
    this.textarea.addEventListener('input', () => this.update());
    this.update();
  }

  update() {
    const length = this.textarea.value.length;
    const percentage = (length / this.maxChars) * 100;

    if (this.counter) {
      this.counter.textContent = `${length} characters`;

      // Update counter color state
      this.counter.classList.remove('warning', 'error');
      if (length > this.maxChars) {
        this.counter.classList.add('error');
      } else if (length > this.maxChars * 0.8) {
        this.counter.classList.add('warning');
      }
    }

    // Update progress bar if it exists
    const progressBar = this.textarea.nextElementSibling?.querySelector('.char-count-progress');
    if (progressBar) {
      progressBar.style.width = Math.min(percentage, 100) + '%';
      progressBar.classList.remove('warning', 'error');
      if (length > this.maxChars) {
        progressBar.classList.add('error');
      } else if (length > this.maxChars * 0.8) {
        progressBar.classList.add('warning');
      }
    }
  }

  isValid() {
    return this.textarea.value.length >= this.minChars && this.textarea.value.length <= this.maxChars;
  }

  getValue() {
    return this.textarea.value;
  }
}

// ============================================
// Loading States
// ============================================

class LoadingManager {
  static show(message = 'Loading...') {
    let overlay = document.querySelector('.loading-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'loading-overlay';
      overlay.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">${message}</span>
                </div>
            `;
      document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
  }

  static hide() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
      overlay.style.display = 'none';
    }
  }

  static setButtonLoading(buttonSelector, isLoading = true) {
    const button = document.querySelector(buttonSelector);
    if (!button) return;

    if (isLoading) {
      button.disabled = true;
      button.classList.add('loading-state');
      button.innerHTML = `<span class="loading-spinner me-2"></span>${button.textContent.split('<span')[0].trim()}`;
    } else {
      button.disabled = false;
      button.classList.remove('loading-state');
      // Note: You might need to restore original text here
    }
  }

  static setFormDisabled(formSelector, disabled = true) {
    const form = document.querySelector(formSelector);
    if (!form) return;

    const inputs = form.querySelectorAll('input, select, textarea, button');
    inputs.forEach(input => {
      input.disabled = disabled;
      input.classList.toggle('loading-state', disabled);
    });
  }
}

// ============================================
// DOM Utilities
// ============================================

class DOMUtils {
  static escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  static truncate(text, length = 50) {
    return text.length > length ? text.substring(0, length) + '...' : text;
  }

  static formatDate(date) {
    const options = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    return new Date(date).toLocaleString('en-US', options);
  }

  static formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  static smoothScroll(element) {
    element.scrollIntoView({behavior: 'smooth', block: 'nearest'});
  }
}

// ============================================
// API Utilities
// ============================================

class APIManager {
  static async request(endpoint, options = {}) {
    try {
      const response = await fetch(endpoint, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  static get(endpoint) {
    return this.request(endpoint, {method: 'GET'});
  }

  static post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  static async uploadFile(endpoint, file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Upload Error:', error);
      throw error;
    }
  }
}

// ============================================
// Font Preset Manager (compact / normal / large)
// ============================================
const FontPresetManager = (function () {
  const STORAGE_KEY = 't2v_font_preset';
  const HTML = document.documentElement;
  const PRESETS = ['compact', 'normal', 'large'];

  // Map of preset -> root font size + CSS custom properties used across the stylesheet.
  const PRESET_CONFIGS = {
    compact: {
      rootFontSize: '14px',
      vars: {
        '--font-xs': '0.75rem',
        '--font-sm': '0.875rem',
        '--font-base': '0.9375rem',
        '--font-md': '1rem',
        '--font-lg': '1.0625rem',
        '--font-xl': '1.125rem',
        '--font-2xl': '1.25rem',
        '--font-3xl': '1.5rem',
        // Spacing scale (smaller for compact)
        '--spacing-xs': '0.2rem',
        '--spacing-sm': '0.4rem',
        '--spacing-md': '0.85rem',
        '--spacing-lg': '1.25rem',
        '--spacing-xl': '1.75rem',
        '--spacing-2xl': '2.5rem',
        '--spacing-3xl': '3rem'
      }
    },
    normal: {
      rootFontSize: '16px',
      vars: {
        '--font-xs': '0.8125rem',
        '--font-sm': '0.9375rem',
        '--font-base': '1rem',
        '--font-md': '1.0625rem',
        '--font-lg': '1.125rem',
        '--font-xl': '1.25rem',
        '--font-2xl': '1.375rem',
        '--font-3xl': '1.75rem',
        // Default spacing (matches CSS :root)
        '--spacing-xs': '0.25rem',
        '--spacing-sm': '0.5rem',
        '--spacing-md': '1rem',
        '--spacing-lg': '1.5rem',
        '--spacing-xl': '2rem',
        '--spacing-2xl': '3rem',
        '--spacing-3xl': '4rem'
      }
    },
    large: {
      rootFontSize: '18px',
      vars: {
        '--font-xs': '0.875rem',
        '--font-sm': '1rem',
        '--font-base': '1.125rem',
        '--font-md': '1.25rem',
        '--font-lg': '1.375rem',
        '--font-xl': '1.625rem',
        '--font-2xl': '1.875rem',
        '--font-3xl': '2.25rem',
        // Spacing scale (larger for large preset)
        '--spacing-xs': '0.3125rem',
        '--spacing-sm': '0.625rem',
        '--spacing-md': '1.125rem',
        '--spacing-lg': '1.75rem',
        '--spacing-xl': '2.5rem',
        '--spacing-2xl': '3.5rem',
        '--spacing-3xl': '5rem'
      }
    }
  };

  function applyPreset(preset) {
    const cfg = PRESET_CONFIGS[preset] || PRESET_CONFIGS.normal;

    // Apply root font-size (affects rem-based inline styles)
    try {
      HTML.style.fontSize = cfg.rootFontSize;
    } catch (e) {
      // ignore
    }

    // Apply CSS variables so stylesheet rules using var(--font-*) update immediately
    try {
      Object.entries(cfg.vars).forEach(([k, v]) => HTML.style.setProperty(k, v));
    } catch (e) {
      // ignore
    }

    // Keep backward-compatible: remove preset-* classes if present
    HTML.classList.remove('preset-compact', 'preset-large');
    if (preset === 'compact') HTML.classList.add('preset-compact');
    if (preset === 'large') HTML.classList.add('preset-large');
  }

  function savePreset(preset) {
    try {
      localStorage.setItem(STORAGE_KEY, preset);
    } catch (e) {
      // ignore storage errors
    }
  }

  function loadPreset() {
    try {
      const p = localStorage.getItem(STORAGE_KEY) || 'normal';
      return PRESETS.includes(p) ? p : 'normal';
    } catch (e) {
      return 'normal';
    }
  }

  function initDropdown() {
    // Attach handler for dropdown items in navbar (delegated)
    document.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-preset]');
      if (!btn) return;
      const preset = btn.getAttribute('data-preset');
      if (!PRESETS.includes(preset)) return;
      setPreset(preset);
    });
  }

  function setPreset(preset) {
    applyPreset(preset);
    savePreset(preset);
    // Optionally show a toast
    try {
      const toast = new ToastNotification();
      toast.info('View size', `Set to ${preset} preset`);
    } catch (e) {
      // ignore
    }
  }

  function getPreset() {
    return loadPreset();
  }

  function init() {
    initDropdown();
    const p = loadPreset();
    applyPreset(p);
  }

  return {
    init,
    setPreset,
    getPreset
  };
})();

// Auto-init font presets as soon as DOM is ready
document.addEventListener('DOMContentLoaded', function () {
  FontPresetManager.init();
});

// ============================================
// Global Initialization
// ============================================

// Initialize global instances
window.toast = new ToastNotification();

// Initialize validators for common forms
document.addEventListener('DOMContentLoaded', function () {
  // Form validators
  if (document.querySelector('#ttsForm')) {
    window.ttsValidator = new FormValidator('#ttsForm');
  }

  // Character counter for text area
  if (document.querySelector('#text')) {
    window.charCounter = new CharacterCounter('#text', '#charCount', 10, 5000);
  }

  // Add accessibility features
  initializeAccessibility();

  // Add keyboard shortcuts
  initializeKeyboardShortcuts();

  // Add theme preference
  initializeThemePreference();
});

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
  // Add skip to main content link
  if (!document.querySelector('.skip-to-main')) {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-to-main btn btn-primary';
    skipLink.textContent = 'Skip to main content';
    skipLink.style.cssText = 'position: absolute; top: -40px; left: 0; z-index: 100;';
    skipLink.onFocus = function () {
      this.style.top = '0';
    };
    skipLink.onBlur = function () {
      this.style.top = '-40px';
    };
    document.body.insertBefore(skipLink, document.body.firstChild);
  }

  // Ensure all interactive elements are keyboard accessible
  const interactiveElements = document.querySelectorAll('.option-card, [role="button"]');
  interactiveElements.forEach(element => {
    if (!element.hasAttribute('tabindex')) {
      element.setAttribute('tabindex', '0');
    }
  });
}

/**
 * Initialize keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
  document.addEventListener('keydown', function (e) {
    // Ctrl/Cmd + Enter to submit form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const form = document.querySelector('form');
      if (form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.click();
        }
      }
    }

    // Escape to close modals
    if (e.key === 'Escape') {
      const modals = document.querySelectorAll('.modal.show');
      modals.forEach(modal => {
        const bootstrapModal = bootstrap.Modal.getInstance(modal);
        if (bootstrapModal) {
          bootstrapModal.hide();
        }
      });
    }
  });
}

/**
 * Initialize theme preference
 */
function initializeThemePreference() {
  // Check for saved theme preference or default to light mode
  const theme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', theme);

  // Add theme toggle if needed
  const themeToggleBtn = document.querySelector('[data-theme-toggle]');
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', function () {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }
}

/**
 * Helper function to show field errors
 */
function showFieldError(fieldName, message) {
  const field = document.querySelector(`[name="${fieldName}"]`);
  if (field) {
    field.classList.add('field-error', 'is-invalid');
    field.classList.remove('field-success', 'is-valid');

    let errorDiv = field.parentElement.querySelector('.field-error-message');
    if (!errorDiv) {
      errorDiv = document.createElement('div');
      errorDiv.className = 'field-error-message';
      field.parentElement.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
  }
}

/**
 * Helper function to clear field errors
 */
function clearFieldError(fieldName) {
  const field = document.querySelector(`[name="${fieldName}"]`);
  if (field) {
    field.classList.remove('field-error', 'is-invalid');
    const errorDiv = field.parentElement.querySelector('.field-error-message');
    if (errorDiv) {
      errorDiv.remove();
    }
  }
}

/**
 * Helper function to disable form submission
 */
function disableFormSubmit(formSelector, disabled = true) {
  const form = document.querySelector(formSelector);
  if (form) {
    const inputs = form.querySelectorAll('input, select, textarea, button');
    inputs.forEach(input => {
      if (input.type !== 'hidden') {
        input.disabled = disabled;
      }
    });
  }
}

/**
 * Ensure SweetAlert appears above Bootstrap modals and close modals before showing alerts.
 */
(function () {
  function closeOpenBootstrapModals() {
    try {
      const openModals = document.querySelectorAll('.modal.show');
      openModals.forEach(modalEl => {
        try {
          const bsInstance = bootstrap.Modal.getInstance(modalEl);
          if (bsInstance) bsInstance.hide();
          else {
            // If no instance, create one and hide it immediately
            const tmp = new bootstrap.Modal(modalEl);
            tmp.hide();
          }
        } catch (e) {
          // ignore
        }
      });
    } catch (e) {
      // ignore
    }
  }

  // Monkey-patch Swal.fire so it first closes any open Bootstrap modals.
  if (window.Swal && typeof Swal.fire === 'function') {
    const _swal = Swal.fire.bind(Swal);
    Swal.fire = function () {
      closeOpenBootstrapModals();
      // Delay slightly to allow Bootstrap hide animations/backdrops to clear.
      const args = arguments;
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          _swal.apply(null, args).then(resolve).catch(reject);
        }, 250);
      });
    };
  } else {
    // If Swal not loaded yet, patch after DOMContentLoaded.
    document.addEventListener('DOMContentLoaded', function () {
      if (window.Swal && typeof Swal.fire === 'function') {
        const _swal = Swal.fire.bind(Swal);
        Swal.fire = function () {
          closeOpenBootstrapModals();
          const args = arguments;
          return new Promise((resolve, reject) => {
            setTimeout(() => {
              _swal.apply(null, args).then(resolve).catch(reject);
            }, 250);
          });
        };
      }
    });
  }
})();

/**
 * Export for use in other modules
 */
window.FormValidator = FormValidator;
window.CharacterCounter = CharacterCounter;
window.LoadingManager = LoadingManager;
window.DOMUtils = DOMUtils;
window.APIManager = APIManager;
window.showFieldError = showFieldError;
window.clearFieldError = clearFieldError;
window.disableFormSubmit = disableFormSubmit;
