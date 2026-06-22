import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

const ConfidenceGauge = ({ value }) => {
  const safeValue = (() => {
    const num = parseFloat(value);
    if (isNaN(num) || !isFinite(num)) return 0;
    if (num <= 1.0) return Math.round(num * 100);
    return Math.round(num);
  })();

  // Use safeValue everywhere in the gauge
  // instead of raw value
  const percentage = Math.min(Math.max(safeValue, 0), 100);
  const circumference = 2 * Math.PI * 45;
  const strokeDash = (percentage / 100) * circumference;
  const color = percentage > 60 ? '#FF4757' 
              : percentage > 40 ? '#FFA502' 
              : '#2ED573';

  return (
    <div className="flex flex-col items-center">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="45"
          fill="none" stroke="rgba(255,255,255,0.1)"
          strokeWidth="10"/>
        <circle cx="60" cy="60" r="45"
          fill="none" stroke={color}
          strokeWidth="10"
          strokeDasharray={`${strokeDash} ${circumference}`}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
          style={{transition: 'stroke-dasharray 0.8s ease'}}
        />
        <text x="60" y="65" textAnchor="middle"
          fill="white" fontSize="18" fontWeight="bold">
          {percentage}%
        </text>
      </svg>
      <p className="text-gray-400 text-sm mt-1">Confidence</p>
    </div>
  );
};

export default ConfidenceGauge;
