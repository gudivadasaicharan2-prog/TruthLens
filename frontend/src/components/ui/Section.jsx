import React from 'react';
import { motion } from 'framer-motion';

/**
 * Reusable Section Component
 * 
 * @param {React.ReactNode} children - Section content
 * @param {string} title - Section title
 * @param {string} subtitle - Section subtitle
 * @param {string} className - Additional CSS classes
 * @param {boolean} centered - Center align content
 * @param {Object} props - Additional props
 */
const Section = ({ 
  children, 
  title, 
  subtitle, 
  className = '',
  centered = false,
  ...props 
}) => {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`py-8 ${className}`}
      {...props}
    >
      {(title || subtitle) && (
        <div className={`mb-6 ${centered ? 'text-center' : ''}`}>
          {title && (
            <h2 className="text-3xl font-bold text-white mb-2 font-['Space_Grotesk']">
              {title}
            </h2>
          )}
          {subtitle && (
            <p className="text-gray-400 text-lg">
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </motion.section>
  );
};

export default Section;
