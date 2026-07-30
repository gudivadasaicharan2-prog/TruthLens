import React from 'react';

/**
 * Skeleton Loader Component
 * 
 * @param {string} className - Additional CSS classes
 * @param {string} variant - Skeleton variant (text, circular, rectangular)
 * @param {number} width - Custom width
 * @param {number} height - Custom height
 */
const Skeleton = ({ className = '', variant = 'rectangular', width, height, ...props }) => {
  const baseClasses = 'animate-pulse bg-card/50 rounded';
  
  const variantClasses = {
    text: 'h-4 w-full',
    circular: 'rounded-full',
    rectangular: 'rounded-xl',
  };
  
  const style = {
    width: width || (variant === 'circular' ? '40px' : '100%'),
    height: height || (variant === 'circular' ? '40px' : variant === 'text' ? '16px' : '100px'),
  };
  
  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
      {...props}
    />
  );
};

export default Skeleton;
