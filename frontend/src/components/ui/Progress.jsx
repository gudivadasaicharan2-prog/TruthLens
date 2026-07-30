import React from 'react';
import { motion } from 'framer-motion';

/**
 * Progress Bar Component
 * 
 * @param {number} value - Progress value (0-100)
 * @param {string} className - Additional CSS classes
 * @param {boolean} animated - Enable animation
 * @param {string} color - Progress bar color (accent, success, warning, danger)
 */
const ProgressBar = ({ value = 0, className = '', animated = true, color = 'accent', ...props }) => {
  const colorClasses = {
    accent: 'bg-accent shadow-glow',
    success: 'bg-success shadow-glow-success',
    warning: 'bg-warning',
    danger: 'bg-danger shadow-glow-danger',
  };
  
  return (
    <div className={`w-full h-2 bg-card/30 rounded-full overflow-hidden ${className}`} {...props}>
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        transition={{ duration: animated ? 0.5 : 0 }}
        className={`h-full rounded-full ${colorClasses[color]}`}
      />
    </div>
  );
};

/**
 * Progress Step Component
 * 
 * @param {string} label - Step label
 * @param {boolean} completed - Step completion status
 * @param {boolean} current - Current step
 * @param {number} index - Step index
 */
const ProgressStep = ({ label, completed = false, current = false, index }) => {
  return (
    <div className="flex items-center gap-4">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
        completed ? 'bg-success shadow-glow-success' : 
        current ? 'bg-accent shadow-glow' : 
        'bg-card/50'
      }`}>
        {completed ? (
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <span className={`text-sm font-medium ${current ? 'text-white' : 'text-text-muted'}`}>
            {index + 1}
          </span>
        )}
      </div>
      <span className={`text-sm ${completed || current ? 'text-text-primary' : 'text-text-muted'}`}>
        {label}
      </span>
    </div>
  );
};

/**
 * Progress Steps Component
 * 
 * @param {Array} steps - Array of step objects { label, completed, current }
 */
const ProgressSteps = ({ steps = [] }) => {
  return (
    <div className="space-y-3">
      {steps.map((step, index) => (
        <ProgressStep
          key={index}
          label={step.label}
          completed={step.completed}
          current={step.current}
          index={index}
        />
      ))}
    </div>
  );
};

export { ProgressBar, ProgressStep, ProgressSteps };
