import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Loader2, Upload, Brain, Eye, FileText, Image as ImageIcon, Zap, Shield, Sparkles } from 'lucide-react';

/**
 * Real-time Analysis Progress Page
 * 
 * Shows websocket-style live progress during image analysis
 */
const AnalysisProgress = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(8);
  
  const analysisSteps = [
    { 
      id: 'upload',
      label: 'Uploading Image', 
      description: 'Securely transferring your image to our servers',
      icon: Upload,
      completed: false, 
      current: false,
      duration: 1.5
    },
    { 
      id: 'load-model',
      label: 'Loading Model', 
      description: 'Initializing EfficientNet-B4 neural network',
      icon: Brain,
      completed: false, 
      current: false,
      duration: 1.2
    },
    { 
      id: 'efficientnet',
      label: 'Running EfficientNet', 
      description: 'Analyzing image features with deep learning',
      icon: Sparkles,
      completed: false, 
      current: false,
      duration: 2.0
    },
    { 
      id: 'face-detection',
      label: 'Running Face Detection', 
      description: 'Identifying faces and facial features',
      icon: Eye,
      completed: false, 
      current: false,
      duration: 1.0
    },
    { 
      id: 'clip',
      label: 'Running CLIP', 
      description: 'Analyzing image-text semantic relationships',
      icon: ImageIcon,
      completed: false, 
      current: false,
      duration: 1.5
    },
    { 
      id: 'forensics',
      label: 'Running Forensics', 
      description: 'Examining pixel-level artifacts and metadata',
      icon: Shield,
      completed: false, 
      current: false,
      duration: 1.8
    },
    { 
      id: 'heatmap',
      label: 'Generating Heatmap', 
      description: 'Creating Grad-CAM visualization',
      icon: Zap,
      completed: false, 
      current: false,
      duration: 1.5
    },
    { 
      id: 'report',
      label: 'Creating Report', 
      description: 'Compiling comprehensive analysis results',
      icon: FileText,
      completed: false, 
      current: false,
      duration: 1.0
    },
    { 
      id: 'finalize',
      label: 'Finalizing Analysis', 
      description: 'Preparing results dashboard',
      icon: CheckCircle,
      completed: false, 
      current: false,
      duration: 0.5
    }
  ];
  
  const [steps, setSteps] = useState(analysisSteps);
  
  useEffect(() => {
    let interval;
    let stepInterval;
    
    // Simulate progress
    interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + Math.random() * 12;
      });
    }, 300);
    
    // Simulate step completion with realistic timing
    stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev >= steps.length - 1) {
          clearInterval(stepInterval);
          // Trigger completion callback
          setTimeout(() => {
            if (onComplete) onComplete();
          }, 800);
          return prev;
        }
        
        setSteps(prevSteps => {
          const newSteps = [...prevSteps];
          newSteps[prev].completed = true;
          newSteps[prev].current = false;
          if (prev + 1 < newSteps.length) {
            newSteps[prev + 1].current = true;
          }
          return newSteps;
        });
        
        // Update estimated time
        setEstimatedTime(prev => Math.max(0, prev - 1.2));
        
        return prev + 1;
      });
    }, 1200);
    
    return () => {
      clearInterval(interval);
      clearInterval(stepInterval);
    };
  }, []);
  
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-3xl"
      >
        {/* Progress Card */}
        <div className="bg-card rounded-2xl p-8 border border-card/50 shadow-glow">
          {/* Header */}
          <div className="text-center mb-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="w-20 h-20 mx-auto mb-4 border-4 border-accent/30 border-t-accent rounded-full flex items-center justify-center"
            >
              <Loader2 className="w-10 h-10 text-accent animate-spin" />
            </motion.div>
            <h2 className="text-3xl font-bold text-text-primary mb-2">
              Analyzing Image
            </h2>
            <p className="text-text-secondary">
              Please wait while our AI processes your image
            </p>
          </div>
          
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between text-sm text-text-secondary mb-2">
              <span>Overall Progress</span>
              <span className="font-mono">{Math.min(100, Math.round(progress))}%</span>
            </div>
            <div className="w-full h-3 bg-card/50 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, progress)}%` }}
                transition={{ duration: 0.3 }}
                className="h-full bg-gradient-to-r from-accent to-blue-600 rounded-full shadow-glow"
              />
            </div>
            <div className="flex justify-between text-xs text-text-muted mt-1">
              <span>Estimated time remaining: ~{estimatedTime.toFixed(1)}s</span>
              <span>Step {currentStep + 1} of {steps.length}</span>
            </div>
          </div>
          
          {/* Steps */}
          <div className="space-y-3">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                    step.completed ? 'bg-success/10 border-success/30' :
                    step.current ? 'bg-accent/10 border-accent/50 shadow-glow' :
                    'bg-card/30 border-card/50'
                  }`}
                >
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    step.completed ? 'bg-success shadow-glow-success' : 
                    step.current ? 'bg-accent shadow-glow' : 
                    'bg-card/50'
                  }`}>
                    {step.completed ? (
                      <CheckCircle className="w-6 h-6 text-white" />
                    ) : step.current ? (
                      <Icon className="w-6 h-6 text-white animate-pulse" />
                    ) : (
                      <Icon className="w-6 h-6 text-text-muted" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`font-medium ${
                        step.completed || step.current ? 'text-text-primary' : 'text-text-muted'
                      }`}>
                        {step.label}
                      </span>
                      {step.current && (
                        <motion.div
                          animate={{ opacity: [0.5, 1, 0.5] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="w-2 h-2 rounded-full bg-accent"
                        />
                      )}
                    </div>
                    <p className={`text-sm ${
                      step.completed || step.current ? 'text-text-secondary' : 'text-text-muted'
                    }`}>
                      {step.description}
                    </p>
                  </div>
                  {step.completed && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="text-success"
                    >
                      <CheckCircle className="w-5 h-5" />
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </div>
          
          {/* Current Status */}
          <div className="mt-8 p-4 bg-glass rounded-xl border border-card/50">
            <AnimatePresence mode="wait">
              {currentStep < steps.length ? (
                <motion.div
                  key="processing"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="flex items-center gap-3"
                >
                  <Loader2 className="w-5 h-5 text-accent animate-spin" />
                  <div>
                    <p className="text-accent font-medium">
                      {steps[currentStep]?.label || 'Processing...'}
                    </p>
                    <p className="text-text-secondary text-sm">
                      {steps[currentStep]?.description || 'Please wait'}
                    </p>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="completed"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex items-center gap-3"
                >
                  <CheckCircle className="w-5 h-5 text-success" />
                  <div>
                    <p className="text-success font-medium">Analysis Complete</p>
                    <p className="text-text-secondary text-sm">Redirecting to results...</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AnalysisProgress;
