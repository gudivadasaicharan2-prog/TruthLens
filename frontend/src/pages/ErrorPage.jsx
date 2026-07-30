import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useRouteError } from 'react-router-dom';
import { AlertTriangle, RefreshCw, Home, ArrowLeft, Bug } from 'lucide-react';

/**
 * Professional Error Page
 * 
 * Displays user-friendly error messages with recovery options
 */
const ErrorPage = ({ errorType = 'general', error = null }) => {
  const navigate = useNavigate();
  const routeError = useRouteError();

  const errorMessages = {
    network: {
      title: 'Connection Error',
      message: 'Unable to connect to our servers. Please check your internet connection and try again.',
      icon: AlertTriangle,
      color: 'text-warning'
    },
    timeout: {
      title: 'Request Timeout',
      message: 'The request took too long to complete. Please try again.',
      icon: AlertTriangle,
      color: 'text-warning'
    },
    unauthorized: {
      title: 'Access Denied',
      message: 'You don\'t have permission to access this resource.',
      icon: AlertTriangle,
      color: 'text-danger'
    },
    notFound: {
      title: 'Page Not Found',
      message: 'The page you\'re looking for doesn\'t exist or has been moved.',
      icon: AlertTriangle,
      color: 'text-accent'
    },
    server: {
      title: 'Server Error',
      message: 'Something went wrong on our end. Our team has been notified.',
      icon: Bug,
      color: 'text-danger'
    },
    offline: {
      title: 'You\'re Offline',
      message: 'Please check your internet connection and try again.',
      icon: AlertTriangle,
      color: 'text-warning'
    },
    general: {
      title: 'Something Went Wrong',
      message: 'An unexpected error occurred. Please try again.',
      icon: AlertTriangle,
      color: 'text-danger'
    }
  };

  const currentError = errorMessages[errorType] || errorMessages.general;
  const Icon = currentError.icon;

  const handleRetry = () => {
    window.location.reload();
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-lg"
      >
        <div className="bg-card rounded-2xl p-8 border border-card/50 shadow-glow text-center">
          {/* Error Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring' }}
            className="w-20 h-20 mx-auto mb-6 rounded-full bg-glass flex items-center justify-center"
          >
            <Icon className={`w-10 h-10 ${currentError.color}`} />
          </motion.div>

          {/* Error Message */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-2xl font-bold text-text-primary mb-2"
          >
            {currentError.title}
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-text-secondary mb-8"
          >
            {currentError.message}
          </motion.p>

          {/* Error Details (in development) */}
          {process.env.NODE_ENV === 'development' && (error || routeError) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="mb-8 p-4 bg-glass-dark rounded-xl border border-card/50 text-left"
            >
              <p className="text-text-muted text-xs font-mono mb-2">Error Details:</p>
              <pre className="text-text-secondary text-xs overflow-auto max-h-32">
                {error?.message || routeError?.message || String(error || routeError)}
              </pre>
            </motion.div>
          )}

          {/* Action Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-3 justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleRetry}
              className="px-6 py-3 bg-accent text-white rounded-xl font-semibold shadow-glow flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" /> Try Again
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleGoBack}
              className="px-6 py-3 bg-glass text-text-primary rounded-xl font-semibold border border-card/50 flex items-center justify-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> Go Back
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleGoHome}
              className="px-6 py-3 bg-glass text-text-secondary rounded-xl font-medium border border-card/50 flex items-center justify-center gap-2"
            >
              <Home className="w-4 h-4" /> Home
            </motion.button>
          </motion.div>

          {/* Support Link */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-text-secondary text-sm mt-6"
          >
            Need help? <a href="mailto:support@truthlens.app" className="text-accent hover:underline">Contact Support</a>
          </motion.p>
        </div>
      </motion.div>
    </div>
  );
};

export default ErrorPage;
