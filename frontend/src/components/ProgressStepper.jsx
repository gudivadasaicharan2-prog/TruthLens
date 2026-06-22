import { motion } from 'framer-motion';
import { Check, Circle, Loader } from 'lucide-react';

const ProgressStepper = ({ steps, currentStep }) => {
  return (
    <div className="flex items-center justify-between w-full max-w-2xl mx-auto">
      {steps.map((step, index) => {
        const isCompleted = index < currentStep;
        const isCurrent = index === currentStep;
        const isPending = index > currentStep;

        return (
          <div key={step.label} className="flex items-center flex-1">
            <div className="flex flex-col items-center">
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-colors ${
                  isCompleted
                    ? 'bg-success border-success text-navy-900'
                    : isCurrent
                    ? 'bg-cyan-400 border-cyan-400 text-navy-900'
                    : 'bg-navy-800 border-navy-700 text-text-secondary'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-6 h-6" />
                ) : isCurrent ? (
                  <Loader className="w-6 h-6 animate-spin" />
                ) : (
                  <Circle className="w-6 h-6" />
                )}
              </motion.div>
              <span
                className={`mt-2 text-sm font-medium ${
                  isCurrent ? 'text-cyan-400' : isCompleted ? 'text-success' : 'text-text-secondary'
                }`}
              >
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div
                className={`flex-1 h-1 mx-4 transition-colors ${
                  isCompleted ? 'bg-success' : 'bg-navy-700'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ProgressStepper;
