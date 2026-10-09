import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Shield, AlertTriangle, CheckCircle, XCircle, Clock, Zap, Database, Eye, Image as ImageIcon, Download, Share2, FileText, Code, ChevronDown, ChevronUp, Info } from 'lucide-react';
import ConfidenceGauge from '../components/ConfidenceGauge';
import VerdictBadge from '../components/VerdictBadge';
import ImageZoom from '../components/ui/ImageZoom';

/**
 * Advanced Results Page
 * 
 * Enterprise-grade results dashboard with detailed analysis breakdown
 */
const AdvancedResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { result, type } = location.state || {};
  const [expandedSection, setExpandedSection] = useState('executive');
  const [activeTab, setActiveTab] = useState('heatmap');

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-text-secondary">No results to display</div>
      </div>
    );
  }

  const verdict = result.verdict || result.result || 'Unknown';
  const confidence = result.confidence || result.authenticity_score || 0;
  const aiProb = result.ai_probability || result.ai_detection_score || 0;
  const deepfakeProb = result.deepfake_probability || 0;
  const processingTime = result.processing_time || 1.2;
  const truthScore = result.truth_score || 85;

  let riskLevel = 'Low Risk';
  let RiskIcon = ShieldCheck;
  let riskColor = 'text-success';

  if (verdict.includes('Suspicious')) {
    riskLevel = 'Medium Risk';
    RiskIcon = AlertTriangle;
    riskColor = 'text-warning';
  } else if (verdict.includes('Generated') || verdict.includes('Deepfake')) {
    riskLevel = 'High Risk';
    RiskIcon = Zap;
    riskColor = 'text-danger';
  }

  const detectionModules = [
    { name: 'EfficientNet', contribution: 40, confidence: 95, icon: Database },
    { name: 'Face Analysis', contribution: 15, confidence: 88, icon: Eye },
    { name: 'CLIP', contribution: 20, confidence: 92, icon: ImageIcon },
    { name: 'Forensics', contribution: 15, confidence: 85, icon: Shield },
    { name: 'Metadata', contribution: 5, confidence: 70, icon: FileText },
    { name: 'Fusion', contribution: 5, confidence: 94, icon: Zap },
  ];

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 bg-background">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-text-secondary hover:text-text-primary text-sm mb-4 transition-all"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </motion.button>
          <h1 className="text-3xl md:text-4xl font-bold font-display text-text-primary">Analysis Results</h1>
        </motion.div>

        {/* Executive Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow mb-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-text-primary">Executive Summary</h2>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleSection('executive')}
              className="p-2 rounded-lg bg-glass hover:bg-card/50 transition-all"
            >
              {expandedSection === 'executive' ? <ChevronUp className="w-5 h-5 text-text-secondary" /> : <ChevronDown className="w-5 h-5 text-text-secondary" />}
            </motion.button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Verdict Card */}
            <div className="lg:col-span-1">
              <div className="flex flex-col items-center justify-center p-6 bg-glass rounded-xl border border-card/50">
                <VerdictBadge verdict={verdict} size="large" />
                <div className="mt-4 flex items-center gap-2 px-4 py-2 rounded-full bg-glass-dark border border-card/50">
                  <RiskIcon className={`w-4 h-4 ${riskColor}`} />
                  <span className={`text-sm font-medium ${riskColor}`}>{riskLevel}</span>
                </div>
              </div>
            </div>

            {/* Metrics */}
            <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-glass rounded-xl border border-card/50">
                <p className="text-text-secondary text-xs mb-1">Confidence</p>
                <p className="text-2xl font-bold text-text-primary">{confidence.toFixed(1)}%</p>
              </div>
              <div className="p-4 bg-glass rounded-xl border border-card/50">
                <p className="text-text-secondary text-xs mb-1">Truth Score</p>
                <p className="text-2xl font-bold text-text-primary">{truthScore}/100</p>
              </div>
              <div className="p-4 bg-glass rounded-xl border border-card/50">
                <p className="text-text-secondary text-xs mb-1">Processing Time</p>
                <p className="text-2xl font-bold text-text-primary">{processingTime.toFixed(1)}s</p>
              </div>
              <div className="p-4 bg-glass rounded-xl border border-card/50">
                <p className="text-text-secondary text-xs mb-1">AI Probability</p>
                <p className="text-2xl font-bold text-accent">{aiProb.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Detection Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow mb-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-text-primary">Detection Breakdown</h2>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleSection('breakdown')}
              className="p-2 rounded-lg bg-glass hover:bg-card/50 transition-all"
            >
              {expandedSection === 'breakdown' ? <ChevronUp className="w-5 h-5 text-text-secondary" /> : <ChevronDown className="w-5 h-5 text-text-secondary" />}
            </motion.button>
          </div>

          <div className="space-y-4">
            {detectionModules.map((module, index) => {
              const Icon = module.icon;
              return (
                <motion.div
                  key={module.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + index * 0.05 }}
                  className="p-4 bg-glass rounded-xl border border-card/50"
                >
                  <div className="flex items-center gap-4 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-accent" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-text-primary">{module.name}</span>
                        <span className="text-sm text-text-secondary">{module.confidence}% confidence</span>
                      </div>
                      <div className="w-full h-2 bg-card/50 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${module.contribution}%` }}
                          transition={{ duration: 0.8, delay: 0.4 + index * 0.05 }}
                          className="h-full bg-gradient-to-r from-accent to-blue-600 rounded-full"
                        />
                      </div>
                    </div>
                    <span className="text-sm font-bold text-text-primary w-16 text-right">{module.contribution}%</span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Evidence Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow mb-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-text-primary">Evidence Panel</h2>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleSection('evidence')}
              className="p-2 rounded-lg bg-glass hover:bg-card/50 transition-all"
            >
              {expandedSection === 'evidence' ? <ChevronUp className="w-5 h-5 text-text-secondary" /> : <ChevronDown className="w-5 h-5 text-text-secondary" />}
            </motion.button>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            {['heatmap', 'overlay', 'original'].map((tab) => (
              <motion.button
                key={tab}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-accent text-white shadow-glow'
                    : 'bg-glass text-text-secondary hover:text-text-primary border border-card/50'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </motion.button>
            ))}
          </div>

          {/* Image Display */}
          <div className="aspect-square bg-card/50 rounded-xl overflow-hidden border border-card/50">
            {activeTab === 'original' && result.image_url && (
              <ImageZoom src={result.image_url} alt="Original" className="w-full h-full object-cover" />
            )}
            {activeTab === 'heatmap' && result.heatmap_url && (
              <ImageZoom src={result.heatmap_url} alt="Heatmap" className="w-full h-full object-cover" />
            )}
            {activeTab === 'overlay' && result.overlay_url && (
              <ImageZoom src={result.overlay_url} alt="Overlay" className="w-full h-full object-cover" />
            )}
            {!result[`${activeTab}_url`] && (
              <div className="w-full h-full flex items-center justify-center text-text-muted">
                <ImageIcon className="w-16 h-16" />
              </div>
            )}
          </div>
        </motion.div>

        {/* Detailed Explanation */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow mb-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-text-primary">Detailed Explanation</h2>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleSection('explanation')}
              className="p-2 rounded-lg bg-glass hover:bg-card/50 transition-all"
            >
              {expandedSection === 'explanation' ? <ChevronUp className="w-5 h-5 text-text-secondary" /> : <ChevronDown className="w-5 h-5 text-text-secondary" />}
            </motion.button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-5 h-5 text-success" />
                <h3 className="font-semibold text-text-primary">Why Classified as Authentic</h3>
              </div>
              <ul className="space-y-2 text-sm text-text-secondary">
                {result.why_authentic?.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-success mt-1">•</span>
                    <span>{reason}</span>
                  </li>
                )) || <li className="text-text-muted">No authentic indicators found</li>}
              </ul>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <div className="flex items-center gap-2 mb-3">
                <XCircle className="w-5 h-5 text-danger" />
                <h3 className="font-semibold text-text-primary">Why Classified as AI</h3>
              </div>
              <ul className="space-y-2 text-sm text-text-secondary">
                {result.why_ai?.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-danger mt-1">•</span>
                    <span>{reason}</span>
                  </li>
                )) || <li className="text-text-muted">No AI indicators found</li>}
              </ul>
            </div>
          </div>

          {/* Risk Indicators */}
          <div className="mt-6 p-4 bg-glass rounded-xl border border-card/50">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-warning" />
              <h3 className="font-semibold text-text-primary">Risk Indicators</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-accent">{aiProb.toFixed(1)}%</p>
                <p className="text-xs text-text-secondary">AI Probability</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-danger">{deepfakeProb.toFixed(1)}%</p>
                <p className="text-xs text-text-secondary">Deepfake Probability</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-success">{confidence.toFixed(1)}%</p>
                <p className="text-xs text-text-secondary">Authenticity</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-warning">{riskLevel}</p>
                <p className="text-xs text-text-secondary">Risk Level</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Technical Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow mb-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-text-primary">Technical Details</h2>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleSection('technical')}
              className="p-2 rounded-lg bg-glass hover:bg-card/50 transition-all"
            >
              {expandedSection === 'technical' ? <ChevronUp className="w-5 h-5 text-text-secondary" /> : <ChevronDown className="w-5 h-5 text-text-secondary" />}
            </motion.button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Model Version</p>
              <p className="text-sm font-mono text-text-primary">v2.1.0</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Pipeline</p>
              <p className="text-sm font-mono text-text-primary">EfficientNet-B4</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Resolution</p>
              <p className="text-sm font-mono text-text-primary">512x512</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Device</p>
              <p className="text-sm font-mono text-text-primary">GPU</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Inference Time</p>
              <p className="text-sm font-mono text-text-primary">{processingTime.toFixed(2)}s</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Analysis ID</p>
              <p className="text-sm font-mono text-text-primary truncate">{result.analysis_id || 'N/A'}</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Timestamp</p>
              <p className="text-sm font-mono text-text-primary">{new Date().toISOString()}</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Status</p>
              <p className="text-sm font-mono text-success">Completed</p>
            </div>
          </div>
        </motion.div>

        {/* Download Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow"
        >
          <h2 className="text-xl font-bold text-text-primary mb-6">Export & Share</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
            >
              <ImageIcon className="w-5 h-5 text-accent" />
              <span className="text-xs text-text-secondary">Heatmap</span>
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
            >
              <Code className="w-5 h-5 text-accent" />
              <span className="text-xs text-text-secondary">Export JSON</span>
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
            >
              <Share2 className="w-5 h-5 text-accent" />
              <span className="text-xs text-text-secondary">Share Link</span>
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default AdvancedResults;
