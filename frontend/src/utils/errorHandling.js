/**
 * Error Handling Utilities
 * 
 * Helper functions for consistent error handling across the application
 */

/**
 * Custom error classes
 */
export class NetworkError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NetworkError';
    this.type = 'network';
  }
}

export class TimeoutError extends Error {
  constructor(message) {
    super(message);
    this.name = 'TimeoutError';
    this.type = 'timeout';
  }
}

export class UnauthorizedError extends Error {
  constructor(message) {
    super(message);
    this.name = 'UnauthorizedError';
    this.type = 'unauthorized';
  }
}

export class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
    this.type = 'validation';
  }
}

/**
 * Parse error type from error object
 */
export const getErrorType = (error) => {
  if (!error) return 'general';
  
  if (error.name === 'NetworkError' || error.message?.includes('network') || error.message?.includes('fetch')) {
    return 'network';
  }
  
  if (error.name === 'TimeoutError' || error.message?.includes('timeout')) {
    return 'timeout';
  }
  
  if (error.status === 401 || error.status === 403 || error.name === 'UnauthorizedError') {
    return 'unauthorized';
  }
  
  if (error.status === 404) {
    return 'notFound';
  }
  
  if (error.status >= 500) {
    return 'server';
  }
  
  return 'general';
};

/**
 * Get user-friendly error message
 */
export const getErrorMessage = (error) => {
  const errorType = getErrorType(error);
  
  const messages = {
    network: 'Unable to connect to our servers. Please check your internet connection.',
    timeout: 'The request took too long to complete. Please try again.',
    unauthorized: 'You don\'t have permission to access this resource.',
    notFound: 'The requested resource was not found.',
    server: 'Something went wrong on our end. Please try again later.',
    general: 'An unexpected error occurred. Please try again.'
  };
  
  return messages[errorType] || messages.general;
};

/**
 * Retry function with exponential backoff
 */
export const retry = async (fn, maxRetries = 3, delay = 1000) => {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // Don't retry on client errors (4xx)
      if (error.status >= 400 && error.status < 500) {
        throw error;
      }
      
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
  }
  
  throw lastError;
};

/**
 * Handle API errors consistently
 */
export const handleApiError = (error) => {
  const errorType = getErrorType(error);
  const message = getErrorMessage(error);
  
  console.error('API Error:', error);
  
  // Show user-friendly notification
  if (typeof window !== 'undefined' && window.showNotification) {
    window.showNotification(message, 'error');
  }
  
  return { errorType, message, originalError: error };
};

/**
 * Check if online
 */
export const isOnline = () => {
  if (typeof navigator !== 'undefined') {
    return navigator.onLine;
  }
  return true;
};

/**
 * Add online/offline event listeners
 */
export const addNetworkListeners = (onOnline, onOffline) => {
  if (typeof window !== 'undefined') {
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }
  return () => {};
};

/**
 * Validate file type
 */
export const validateFileType = (file, allowedTypes = ['image/jpeg', 'image/png', 'image/webp']) => {
  if (!file) return false;
  return allowedTypes.includes(file.type);
};

/**
 * Validate file size
 */
export const validateFileSize = (file, maxSizeMB = 10) => {
  if (!file) return false;
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
};

/**
 * Get file validation error
 */
export const getFileValidationError = (file, allowedTypes, maxSizeMB) => {
  if (!file) {
    return 'No file selected';
  }
  
  if (!validateFileType(file, allowedTypes)) {
    return `Invalid file type. Allowed types: ${allowedTypes.join(', ')}`;
  }
  
  if (!validateFileSize(file, maxSizeMB)) {
    return `File size exceeds ${maxSizeMB}MB limit`;
  }
  
  return null;
};

/**
 * Safe JSON parse
 */
export const safeJsonParse = (str, defaultValue = null) => {
  try {
    return JSON.parse(str);
  } catch (error) {
    console.error('JSON parse error:', error);
    return defaultValue;
  }
};

/**
 * Safe localStorage operations
 */
export const safeLocalStorage = {
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('localStorage get error:', error);
      return defaultValue;
    }
  },
  
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('localStorage set error:', error);
      return false;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error('localStorage remove error:', error);
      return false;
    }
  }
};
