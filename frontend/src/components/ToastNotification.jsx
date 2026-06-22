import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { useEffect, useState } from 'react';

const ToastNotification = ({ message, type = 'success', onClose, duration = 3000 }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300);
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const getStyles = (type) => {
    switch (type) {
      case 'success':
        return {
          bg: 'bg-success/20',
          border: 'border-success/50',
          icon: CheckCircle,
          iconColor: 'text-success'
        };
      case 'error':
        return {
          bg: 'bg-danger/20',
          border: 'border-danger/50',
          icon: AlertCircle,
          iconColor: 'text-danger'
        };
      case 'info':
        return {
          bg: 'bg-cyan-400/20',
          border: 'border-cyan-400/50',
          icon: Info,
          iconColor: 'text-cyan-400'
        };
      default:
        return {
          bg: 'bg-navy-800',
          border: 'border-navy-700',
          icon: Info,
          iconColor: 'text-text-secondary'
        };
    }
  };

  const styles = getStyles(type);
  const Icon = styles.icon;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -50, x: '-50%' }}
          animate={{ opacity: 1, y: 0, x: '-50%' }}
          exit={{ opacity: 0, y: -50, x: '-50%' }}
          className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-6 py-4 rounded-lg border backdrop-blur-lg flex items-center space-x-3 ${styles.bg} ${styles.border}`}
        >
          <Icon className={`w-5 h-5 ${styles.iconColor}`} />
          <span className="text-text-primary font-medium">{message}</span>
          <button
            onClick={() => {
              setIsVisible(false);
              setTimeout(onClose, 300);
            }}
            className="ml-4 text-text-secondary hover:text-text-primary"
          >
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ToastNotification;
