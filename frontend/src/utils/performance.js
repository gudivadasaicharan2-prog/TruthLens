/**
 * Performance Utilities
 * 
 * Helper functions for optimizing application performance
 */

/**
 * Debounce function to limit the rate of function calls
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Throttle function to limit the rate of function calls
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Memoize expensive function calls
 */
export const memoize = (fn) => {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
};

/**
 * Image caching utility
 */
class ImageCache {
  constructor(maxSize = 50) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  get(url) {
    return this.cache.get(url);
  }

  set(url, blob) {
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(url, blob);
  }

  clear() {
    this.cache.clear();
  }

  has(url) {
    return this.cache.has(url);
  }
}

export const imageCache = new ImageCache();

/**
 * Lazy load images with Intersection Observer
 */
export const lazyLoadImage = (img, src) => {
  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = src;
        img.classList.remove('lazy');
        obs.unobserve(img);
      }
    });
  });

  observer.observe(img);
};

/**
 * Preload critical resources
 */
export const preloadResource = (url, as = 'script') => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.href = url;
  link.as = as;
  document.head.appendChild(link);
};

/**
 * Measure component render time
 */
export const measureRender = (componentName, fn) => {
  const start = performance.now();
  const result = fn();
  const end = performance.now();
  console.log(`${componentName} render time: ${(end - start).toFixed(2)}ms`);
  return result;
};

/**
 * Check if user is on slow connection
 */
export const isSlowConnection = () => {
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  if (!connection) return false;
  return connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g';
};

/**
 * Optimize image loading based on connection
 */
export const getOptimizedImageUrl = (url, connectionType) => {
  if (!connectionType) {
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    connectionType = connection?.effectiveType;
  }

  if (connectionType === 'slow-2g' || connectionType === '2g') {
    // Return low quality version
    return url + '?quality=low';
  }
  
  if (connectionType === '3g') {
    // Return medium quality version
    return url + '?quality=medium';
  }

  return url;
};

/**
 * Virtual scroll helper for large lists
 */
export const virtualScroll = {
  getItemOffset: (index, itemHeight) => index * itemHeight,
  getItemIndex: (scrollTop, itemHeight) => Math.floor(scrollTop / itemHeight),
  getVisibleRange: (scrollTop, containerHeight, itemHeight) => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / itemHeight) + 1,
      1000 // Max items
    );
    return { startIndex, endIndex };
  }
};

/**
 * Web Worker for background processing
 */
export const createWorker = (fn) => {
  const blob = new Blob([`(${fn.toString()})()`], { type: 'application/javascript' });
  return new Worker(URL.createObjectURL(blob));
};

/**
 * Request animation frame throttle
 */
export const rafThrottle = (fn) => {
  let lastArgs = null;
  let lastFrame = null;

  return (...args) => {
    lastArgs = args;
    if (!lastFrame) {
      lastFrame = requestAnimationFrame(() => {
        fn(...lastArgs);
        lastFrame = null;
        lastArgs = null;
      });
    }
  };
};
