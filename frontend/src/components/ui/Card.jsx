import React from 'react';
import { motion } from 'framer-motion';

/**
 * Reusable Glassmorphism Card Component
 * 
 * @param {React.ReactNode} children - Card content
 * @param {string} className - Additional CSS classes
 * @param {boolean} hover - Enable hover effect
 * @param {boolean} xl - Use extra large variant
 * @param {Object} props - Additional props
 */
const Card = ({ children, className = '', hover = false, xl = false, ...props }) => {
  const baseClasses = xl ? 'glass-card-xl' : 'glass-card';
  const hoverClasses = hover 
    ? 'hover:scale-[1.02] hover:border-white/20 transition-all duration-300 cursor-pointer' 
    : '';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`${baseClasses} ${hoverClasses} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default Card;
