import { motion } from 'framer-motion';

const ScanAnimation = ({ children, isScanning }) => {
  return (
    <div className="relative overflow-hidden rounded-lg">
      {children}
      {isScanning && (
        <motion.div
          className="absolute top-0 left-0 right-0 h-1 bg-cyan-400 shadow-lg shadow-cyan-400/50"
          initial={{ top: '0%' }}
          animate={{ top: '100%' }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'linear',
          }}
          style={{
            boxShadow: '0 0 20px 5px rgba(0, 212, 255, 0.5)',
          }}
        />
      )}
    </div>
  );
};

export default ScanAnimation;
