import React from 'react';
import { motion } from 'framer-motion';

/**
 * Reusable Button Component
 * 
 * @param {React.ReactNode} children - Button content
 * @param {string} variant - Button variant: 'primary', 'secondary', 'accent', 'success', 'danger', 'warning', 'ghost'
 * @param {string} size - Button size: 'sm', 'md', 'lg'
 * @param {boolean} disabled - Disable button
 * @param {string} className - Additional CSS classes
 * @param {Function} onClick - Click handler
 * @param {Object} props - Additional props
 */
const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  disabled = false,
  className = '',
  onClick,
  ...props 
}) => {
  const variants = {
    primary: 'bg-blue-500 hover:bg-blue-600 text-white border-blue-500/50',
    secondary: 'bg-purple-500 hover:bg-purple-600 text-white border-purple-500/50',
    accent: 'bg-cyan-500 hover:bg-cyan-600 text-white border-cyan-500/50',
    success: 'bg-emerald-500 hover:bg-emerald-600 text-white border-emerald-500/50',
    danger: 'bg-red-500 hover:bg-red-600 text-white border-red-500/50',
    warning: 'bg-amber-500 hover:bg-amber-600 text-white border-amber-500/50',
    ghost: 'bg-white/5 hover:bg-white/10 text-white border-white/20',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      disabled={disabled}
      onClick={onClick}
      className={`
        ${variants[variant]}
        ${sizes[size]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        rounded-xl border font-medium transition-all duration-200
        backdrop-blur-sm
        ${className}
      `}
      {...props}
    >
      {children}
    </motion.button>
  );
};

export default Button;
