import { motion } from 'framer-motion';

const VerdictBadge = ({ verdict }) => {
  const getStyles = (verdict) => {
    switch (verdict?.toLowerCase()) {
      case 'fake':
      case 'deepfake':
      case 'ai-generated':
      case 'false':
        return {
          bg: 'bg-danger/20',
          border: 'border-danger/50',
          text: 'text-danger',
          icon: '✕'
        };
      case 'real':
      case 'authentic':
      case 'true':
      case 'likely authentic':
      case 'likely true':
        return {
          bg: 'bg-success/20',
          border: 'border-success/50',
          text: 'text-success',
          icon: '✓'
        };
      case 'suspicious':
      case 'partially false':
      case 'possibly manipulated':
      case 'possibly deepfake':
        return {
          bg: 'bg-warning/20',
          border: 'border-warning/50',
          text: 'text-warning',
          icon: '!'
        };
      case 'not applicable':
        return {
          bg: 'bg-blue-500/20',
          border: 'border-blue-500/50',
          text: 'text-blue-400',
          icon: 'ℹ️'
        };
      case 'unverified':
        return {
          bg: 'bg-gray-500/20',
          border: 'border-gray-500/50',
          text: 'text-gray-400',
          icon: '?'
        };
      default:
        return {
          bg: 'bg-gray-500/20',
          border: 'border-gray-500/50',
          text: 'text-gray-400',
          icon: '?'
        };
    }
  };

  const styles = getStyles(verdict);

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full border ${styles.bg} ${styles.border} ${styles.text}`}
    >
      <span className="font-bold">{styles.icon}</span>
      <span className="font-heading font-semibold">{verdict || 'Unknown'}</span>
    </motion.div>
  );
};

export default VerdictBadge;
