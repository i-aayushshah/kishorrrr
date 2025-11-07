document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const yearEl = document.getElementById('year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  /**
   * Mobile navigation drawer
   */
  const navPanel = document.querySelector('[data-mobile-nav]');
  const navToggle = document.querySelector('[data-mobile-nav-toggle]');
  const navOverlay = document.querySelector('[data-mobile-nav-overlay]');
  const navClose = document.querySelector('[data-mobile-nav-close]');
  const navLinks = document.querySelectorAll('[data-mobile-nav-link]');

  const closeNav = () => {
    if (!navPanel) return;
    navPanel.classList.add('hidden');
    navPanel.setAttribute('aria-hidden', 'true');
    body.removeAttribute('data-mobile-nav-open');
    navOverlay?.classList.add('hidden');
  };

  const openNav = () => {
    if (!navPanel) return;
    navPanel.classList.remove('hidden');
    navPanel.setAttribute('aria-hidden', 'false');
    body.setAttribute('data-mobile-nav-open', 'true');
    navOverlay?.classList.remove('hidden');
  };

  navToggle?.addEventListener('click', () => {
    if (navPanel?.classList.contains('hidden')) {
      openNav();
    } else {
      closeNav();
    }
  });

  navClose?.addEventListener('click', closeNav);
  navOverlay?.addEventListener('click', closeNav);
  navLinks.forEach(link => link.addEventListener('click', closeNav));

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      closeNav();
    }
  });

  /**
   * Flash notifications
   */
  document.querySelectorAll('[data-dismiss-flash]').forEach(button => {
    button.addEventListener('click', () => {
      const flash = button.closest('[data-flash]');
      if (flash) {
        flash.classList.add('opacity-0', 'translate-y-[-8px]');
        setTimeout(() => flash.remove(), 200);
      }
    });
  });

  // Auto-dismiss flash notifications after 5 seconds
  document.querySelectorAll('[data-flash]').forEach(flash => {
    setTimeout(() => {
      flash.classList.add('opacity-0', 'translate-y-[-8px]');
      setTimeout(() => flash.remove(), 200);
    }, 5000);
  });

  /**
   * Upload preview + submit affordance
   */
  const fileInput = document.querySelector('[data-upload-input]');
  const previewWrapper = document.querySelector('[data-preview]');
  const previewImage = previewWrapper?.querySelector('[data-preview-img]');
  const previewName = previewWrapper?.querySelector('[data-preview-name]');

  if (fileInput && previewWrapper && previewImage) {
    const resetPreviewState = () => {
      previewWrapper.classList.add('hidden');
      previewImage.src = '';
      previewImage.classList.remove('is-ready');
      if (previewName) {
        previewName.textContent = '';
      }
    };

    fileInput.addEventListener('change', () => {
      const [file] = fileInput.files || [];
      if (!file) {
        resetPreviewState();
        return;
      }

      const reader = new FileReader();
      reader.addEventListener('load', event => {
        previewImage.src = event.target?.result || '';
        previewWrapper.classList.remove('hidden');
        requestAnimationFrame(() => previewImage.classList.add('is-ready'));
      });
      reader.readAsDataURL(file);

      if (previewName) {
        previewName.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`;
      }
    });
  }

  /**
   * Analyze button loading state
   */
  const analyzeForm = document.getElementById('analyzeForm');
  const analyzeBtn = document.getElementById('analyzeBtn');

  if (analyzeForm && analyzeBtn) {
    analyzeForm.addEventListener('submit', () => {
      analyzeBtn.setAttribute('disabled', 'true');
      analyzeBtn.classList.add('opacity-80');
      const label = analyzeBtn.querySelector('[data-label]');
      const spinner = analyzeBtn.querySelector('[data-spinner]');
      label?.classList.add('hidden');
      spinner?.classList.remove('hidden');
    });
  }

  /**
   * Modal dialogs
   */
  const dialogRegistry = new Map();
  document.querySelectorAll('[data-dialog]').forEach(dialog => {
    const id = dialog.getAttribute('data-dialog');
    if (!id) return;
    dialogRegistry.set(id, dialog);
  });

  const setDialogState = (dialog, open) => {
    if (!dialog) return;
    if (open) {
      dialog.classList.remove('hidden');
      dialog.setAttribute('aria-hidden', 'false');
      body.setAttribute('data-dialog-open', 'true');
    } else {
      dialog.classList.add('hidden');
      dialog.setAttribute('aria-hidden', 'true');
      if (![...dialogRegistry.values()].some(node => !node.classList.contains('hidden'))) {
        body.removeAttribute('data-dialog-open');
      }
    }
  };

  document.querySelectorAll('[data-dialog-open]').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const target = trigger.getAttribute('data-dialog-open');
      setDialogState(dialogRegistry.get(target), true);
    });
  });

  document.querySelectorAll('[data-dialog-close]').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const target = trigger.getAttribute('data-dialog-close');
      setDialogState(dialogRegistry.get(target), false);
    });
  });

  dialogRegistry.forEach(dialog => {
    dialog.addEventListener('click', event => {
      if (event.target === dialog) {
        setDialogState(dialog, false);
      }
    });
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      dialogRegistry.forEach(dialog => setDialogState(dialog, false));
    }
  });

  /**
   * Password confirmation helper
   */
  const passwordInput = document.querySelector('[data-password-input]');
  const confirmInput = document.querySelector('[data-confirm-input]');

  const validatePasswordMatch = () => {
    if (!passwordInput || !confirmInput) return;
    if (confirmInput.value === '') {
      confirmInput.setCustomValidity('');
      return;
    }
    const match = passwordInput.value === confirmInput.value;
    confirmInput.setCustomValidity(match ? '' : 'Passwords must match');
  };

  if (passwordInput && confirmInput) {
    passwordInput.addEventListener('input', validatePasswordMatch);
    confirmInput.addEventListener('input', validatePasswordMatch);
    validatePasswordMatch();
  }

  /**
   * Password visibility toggles
   */
  const togglePasswordVisibility = (input, button) => {
    const isPassword = input.getAttribute('type') === 'password';
    input.setAttribute('type', isPassword ? 'text' : 'password');
    const visibleIcon = button.querySelector('[data-icon-visible]');
    const hiddenIcon = button.querySelector('[data-icon-hidden]');
    if (visibleIcon && hiddenIcon) {
      visibleIcon.classList.toggle('hidden', !isPassword);
      hiddenIcon.classList.toggle('hidden', isPassword);
    }
    button.setAttribute('aria-pressed', String(isPassword));
  };

  document.querySelectorAll('[data-password-toggle]').forEach(button => {
    const selector = button.getAttribute('data-password-toggle');
    if (!selector) return;
    const input = document.querySelector(selector);
    if (!input) return;

    button.addEventListener('click', () => {
      togglePasswordVisibility(input, button);
    });

    // Ensure the correct icon state on load (in case browsers autofill).
    requestAnimationFrame(() => {
      const isPassword = input.getAttribute('type') === 'password';
      const visibleIcon = button.querySelector('[data-icon-visible]');
      const hiddenIcon = button.querySelector('[data-icon-hidden]');
      if (visibleIcon && hiddenIcon) {
        visibleIcon.classList.toggle('hidden', !isPassword);
        hiddenIcon.classList.toggle('hidden', isPassword);
      }
    });
  });
});
