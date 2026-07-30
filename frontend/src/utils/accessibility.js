/**
 * Accessibility Utilities
 * 
 * Helper functions for improving accessibility across the application
 */

/**
 * Generate unique IDs for ARIA labels
 */
export const generateId = (prefix) => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Handle keyboard navigation for custom components
 */
export const handleKeyDown = (event, action) => {
  switch (event.key) {
    case 'Enter':
    case ' ':
      event.preventDefault();
      action();
      break;
    case 'Escape':
      event.preventDefault();
      // Handle escape if needed
      break;
    default:
      break;
  }
};

/**
 * Announce screen reader messages
 */
export const announce = (message) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Focus trap for modals
 */
export const trapFocus = (element) => {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  const handleTab = (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable.focus();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    }
  };

  element.addEventListener('keydown', handleTab);
  
  return () => {
    element.removeEventListener('keydown', handleTab);
  };
};

/**
 * Skip to main content link
 */
export const createSkipLink = () => {
  const skipLink = document.createElement('a');
  skipLink.href = '#main-content';
  skipLink.textContent = 'Skip to main content';
  skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-accent focus:text-white focus:rounded-lg';
  document.body.insertBefore(skipLink, document.body.firstChild);
  
  const mainContent = document.getElementById('main-content');
  if (mainContent) {
    mainContent.setAttribute('tabindex', '-1');
  }
};

/**
 * Get ARIA label for common actions
 */
export const getAriaLabel = (action, context) => {
  const labels = {
    upload: 'Upload image for analysis',
    analyze: 'Analyze image',
    download: 'Download report',
    share: 'Share analysis',
    delete: 'Delete analysis',
    view: 'View analysis details',
    close: 'Close dialog',
    menu: 'Open menu',
    settings: 'Open settings',
    filter: 'Filter results',
    sort: 'Sort results',
    search: 'Search',
    compare: 'Compare images',
    batch: 'Batch analysis',
  };

  return context ? `${labels[action]} for ${context}` : labels[action];
};

/**
 * Check if high contrast mode is enabled
 */
export const isHighContrast = () => {
  return window.matchMedia('(prefers-contrast: high)').matches;
};

/**
 * Check if reduced motion is preferred
 */
export const prefersReducedMotion = () => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Check if screen reader is being used
 */
export const isScreenReader = () => {
  // This is a heuristic - not 100% reliable
  return window.speechSynthesis && window.speechSynthesis.getVoices().length > 0;
};
