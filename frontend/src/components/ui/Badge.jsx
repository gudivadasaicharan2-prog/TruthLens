import React from 'react';
import { motion } from 'framer-motion';

/**
 * Reusable Badge Component
 * 
 * @param {React.ReactNode} children - Badge content
 * @param {string} variant - Badge variant: 'primary', 'secondary', 'accent', 'success', 'danger', 'warning', 'neutral'
 * @param {string} size - Badge size: 'sm', 'md', 'lg'
 * @param {string} className - Additional CSS classes
 * @param {Object} props - Additional props
 */
const Badge = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  className = '',
  ...props 
}) => {
  const variants = {
    primary: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    secondary: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    accent: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    success: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    danger: 'bg-red-500/20 text-red-400 border-red-500/30',
    warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    neutral: 'bg-white/10 text-gray-300 border-white/20',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <motion.span
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`
        ${variants[variant]}
        ${sizes[size]}
        rounded-full border font-medium
        backdrop-blur-sm
        ${className}
      `}
      {...props}
    >
      {children}
    </motion.span>
  );
};

export default Badge;
