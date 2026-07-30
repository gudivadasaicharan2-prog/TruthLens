import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ConfidenceGauge from '../components/ConfidenceGauge';
import VerdictBadge from '../components/VerdictBadge';
import ImageZoom from '../components/ui/ImageZoom';
import { ChevronDown, AlertTriangle, ShieldCheck, ShieldAlert, Zap, ArrowLeft, Download, FileText, Image as ImageIcon, Code, History, Settings, Info, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const Results = () => {
  const location = useLocation();
  const { result, type } = location.state || {};
  const [showAdvanced, setShowAdvanced] = useState(false);

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
  const findings = result.key_findings || result.reasons || result.issues || [];
  const metadata = result.metadata_summary || {};
  
  let riskLevel = 'Unknown Risk';
  let RiskIcon = ShieldAlert;
  let riskColor = 'text-text-secondary';
  
  if (verdict.includes('Authentic')) {
    riskLevel = 'Low Risk';
    RiskIcon = ShieldCheck;
    riskColor = 'text-success';
  } else if (verdict.includes('Suspicious')) {
    riskLevel = 'Medium Risk';
    RiskIcon = AlertTriangle;
    riskColor = 'text-warning';
  } else if (verdict.includes('Generated') || verdict.includes('Deepfake')) {
    riskLevel = 'High Risk';
    RiskIcon = Zap;
    riskColor = 'text-danger';
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 bg-background">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => window.history.back()}
            className="flex items-center gap-2 text-text-secondary hover:text-text-primary text-sm mb-4 transition-all"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </motion.button>
          <h1 className="text-3xl md:text-4xl font-bold font-display text-text-primary">Analysis Results</h1>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card-xl p-6 md:p-8"
        >
          {/* Top Section: Verdict & Confidence */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-8 mb-8 pb-8 border-b border-card/50">
            <div className="flex flex-col items-center md:items-start gap-4">
              <VerdictBadge verdict={verdict} />
              <motion.div
                whileHover={{ scale: 1.05 }}
                className={`flex items-center gap-2 px-4 py-2 rounded-full bg-glass-dark border border-card/50 ${riskColor}`}
              >
                <RiskIcon className="w-4 h-4" />
                <span className="text-sm font-medium">{riskLevel}</span>
              </motion.div>
            </div>
            
            <ConfidenceGauge value={confidence} />
          </div>

          {/* Visualization Section */}
          <div className="mb-8 pb-8 border-b border-card/50">
            <h3 className="text-lg font-bold text-text-primary mb-4 font-display">Visualization</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <p className="text-xs text-text-secondary uppercase tracking-wider">Original Image</p>
                <div className="aspect-square bg-card/50 rounded-xl overflow-hidden border border-card/50">
                  {result.image_url ? (
                    <ImageZoom src={result.image_url} alt="Original" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-text-muted">
                      <ImageIcon className="w-8 h-8" />
                    </div>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-xs text-text-secondary uppercase tracking-wider">Grad-CAM Heatmap</p>
                <div className="aspect-square bg-card/50 rounded-xl overflow-hidden border border-card/50">
                  {result.heatmap_url ? (
                    <ImageZoom src={result.heatmap_url} alt="Heatmap" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-text-muted">
                      <ImageIcon className="w-8 h-8" />
                    </div>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-xs text-text-secondary uppercase tracking-wider">Overlay</p>
                <div className="aspect-square bg-card/50 rounded-xl overflow-hidden border border-card/50">
                  {result.overlay_url ? (
                    <ImageZoom src={result.overlay_url} alt="Overlay" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-text-muted">
                      <ImageIcon className="w-8 h-8" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Key Findings */}
          {findings.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mb-8"
            >
              <h3 className="text-lg font-bold text-text-primary mb-4 font-display">Key Findings</h3>
              <div className="space-y-3">
                {findings.map((finding, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + idx * 0.05 }}
                    whileHover={{ scale: 1.01, x: 4 }}
                    className="flex items-start gap-3 p-4 bg-glass rounded-xl cursor-pointer border border-card/50"
                  >
                    <span className={`text-lg leading-none ${finding.startsWith('✓') ? 'text-success' : finding.startsWith('✗') ? 'text-danger' : 'text-accent'}`}>
                      {finding.charAt(0)}
                    </span>
                    <span className="text-text-secondary text-sm leading-relaxed">{finding.substring(1).trim()}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Explanation Section */}
          <div className="mb-8 pb-8 border-b border-card/50">
            <h3 className="text-lg font-bold text-text-primary mb-4 font-display">Explanation</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-glass rounded-xl border border-card/50">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-5 h-5 text-success" />
                  <h4 className="font-semibold text-text-primary">Why Authentic</h4>
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
                  <h4 className="font-semibold text-text-primary">Why AI</h4>
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
          </div>

          {/* Analysis Modules */}
          <div className="mb-8 pb-8 border-b border-card/50">
            <h3 className="text-lg font-bold text-text-primary mb-4 font-display">Analysis Modules</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {[
                { name: 'EfficientNet', status: 'completed', confidence: 95, contribution: 40 },
                { name: 'Face Detection', status: 'completed', confidence: 88, contribution: 15 },
                { name: 'CLIP', status: 'completed', confidence: 92, contribution: 20 },
                { name: 'Forensics', status: 'completed', confidence: 85, contribution: 15 },
                { name: 'Metadata', status: 'completed', confidence: 70, contribution: 5 },
                { name: 'Fusion Engine', status: 'completed', confidence: 94, contribution: 5 },
              ].map((module, idx) => (
                <motion.div
                  key={module.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + idx * 0.05 }}
                  className="p-3 bg-glass rounded-xl border border-card/50 text-center"
                >
                  <div className={`w-2 h-2 rounded-full mx-auto mb-2 ${module.status === 'completed' ? 'bg-success shadow-glow-success' : 'bg-warning'}`} />
                  <p className="text-xs font-semibold text-text-primary mb-1">{module.name}</p>
                  <p className="text-xs text-text-secondary">{module.confidence}%</p>
                  <p className="text-xs text-text-muted">{module.contribution}%</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Advanced Analysis Accordion */}
          <div className="mt-8 border-t border-card/50 pt-6">
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full p-4 bg-glass-dark rounded-xl transition-all border border-card/50"
            >
              <span className="font-bold text-text-secondary">Advanced Analysis & Metadata</span>
              <motion.div
                animate={{ rotate: showAdvanced ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="w-5 h-5 text-text-secondary" />
              </motion.div>
            </motion.button>
            
            <AnimatePresence>
              {showAdvanced && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Probabilities */}
                    <div className="space-y-4">
                      <h4 className="text-sm font-bold text-text-secondary uppercase tracking-wider">Detection Scores</h4>
                      <div className="p-4 bg-glass rounded-xl space-y-3 border border-card/50">
                        <div className="flex justify-between items-center">
                          <span className="text-text-secondary text-sm">AI Probability</span>
                          <span className="text-text-primary font-mono">{aiProb.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-card/50 rounded-full h-1.5">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${aiProb}%` }}
                            transition={{ duration: 0.8 }}
                            className="bg-gradient-to-r from-warning to-danger h-1.5 rounded-full"
                          />
                        </div>
                        
                        <div className="flex justify-between items-center pt-2">
                          <span className="text-text-secondary text-sm">Deepfake Probability</span>
                          <span className="text-text-primary font-mono">{deepfakeProb.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-card/50 rounded-full h-1.5">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${deepfakeProb}%` }}
                            transition={{ duration: 0.8, delay: 0.2 }}
                            className="bg-gradient-to-r from-danger to-rose-500 h-1.5 rounded-full"
                          />
                        </div>
                      </div>
                    </div>
                    
                    {/* Metadata */}
                    <div className="space-y-4">
                      <h4 className="text-sm font-bold text-text-secondary uppercase tracking-wider">File Metadata</h4>
                      <div className="p-4 bg-glass rounded-xl space-y-2 border border-card/50">
                        {Object.entries(metadata).length > 0 ? (
                          Object.entries(metadata).map(([key, val]) => (
                            <div key={key} className="flex justify-between items-start gap-4">
                              <span className="text-text-secondary text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                              <span className="text-text-primary text-sm text-right font-mono truncate max-w-[200px]">{String(val)}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-text-secondary text-sm">No advanced metadata available.</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Downloads Section */}
                  <div className="mt-6 pt-6 border-t border-card/50">
                    <h4 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-4">Download Reports</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
                      >
                        <FileText className="w-5 h-5 text-accent" />
                        <span className="text-xs text-text-secondary">PDF Report</span>
                      </motion.button>
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
                        <ImageIcon className="w-5 h-5 text-accent" />
                        <span className="text-xs text-text-secondary">Overlay</span>
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
                      >
                        <Code className="w-5 h-5 text-accent" />
                        <span className="text-xs text-text-secondary">Export JSON</span>
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
        </motion.div>
      </div>
    </div>
  );
};

export default Results;
