import React, { useCallback, useState } from 'react';
import { motion } from 'framer-motion';

/**
 * Upload Zone Component
 * 
 * @param {Function} onFileSelect - Callback when file is selected
 * @param {boolean} isDragging - Drag state
 * @param {string} className - Additional CSS classes
 */
const UploadZone = ({ onFileSelect, isDragging = false, className = '', ...props }) => {
  const [dragOver, setDragOver] = useState(false);
  
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }, []);
  
  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);
  
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0 && onFileSelect) {
      onFileSelect(files[0]);
    }
  }, [onFileSelect]);
  
  const handleFileInput = useCallback((e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0 && onFileSelect) {
      onFileSelect(files[0]);
    }
  }, [onFileSelect]);
  
  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        relative border-2 border-dashed rounded-2xl p-12
        transition-all duration-300 cursor-pointer
        ${dragOver ? 'border-accent bg-accent/10' : 'border-card/50 bg-card/30 hover:border-accent/50'}
        ${className}
      `}
      {...props}
    >
      <input
        type="file"
        accept="image/*"
        onChange={handleFileInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      
      <div className="flex flex-col items-center justify-center text-center">
        <motion.div
          animate={dragOver ? { scale: 1.1, rotate: 5 } : { scale: 1, rotate: 0 }}
          transition={{ duration: 0.2 }}
          className="mb-6"
        >
          <svg className="w-16 h-16 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </motion.div>
        
        <h3 className="text-xl font-semibold text-text-primary mb-2">
          {dragOver ? 'Drop your image here' : 'Upload your image'}
        </h3>
        
        <p className="text-text-secondary mb-4">
          Drag and drop or click to browse
        </p>
        
        <div className="flex gap-2 text-xs text-text-muted">
          <span className="px-2 py-1 bg-card/50 rounded">JPG</span>
          <span className="px-2 py-1 bg-card/50 rounded">PNG</span>
          <span className="px-2 py-1 bg-card/50 rounded">WEBP</span>
          <span className="px-2 py-1 bg-card/50 rounded">BMP</span>
        </div>
      </div>
    </motion.div>
  );
};

export default UploadZone;
