import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ConfidenceGauge from '../components/ConfidenceGauge';
import VerdictBadge from '../components/VerdictBadge';
import { ChevronDown, AlertTriangle, ShieldCheck, ShieldAlert, Zap, ArrowLeft } from 'lucide-react';

const Results = () => {
  const location = useLocation();
  const { result, type } = location.state || {};
  const [showAdvanced, setShowAdvanced] = useState(false);

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--background)' }}>
        <div className="text-muted-foreground">No results to display</div>
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
  let riskColor = 'text-muted-foreground';
  
  if (verdict.includes('Authentic')) {
    riskLevel = 'Low Risk';
    RiskIcon = ShieldCheck;
    riskColor = 'text-emerald-400';
  } else if (verdict.includes('Suspicious')) {
    riskLevel = 'Medium Risk';
    RiskIcon = AlertTriangle;
    riskColor = 'text-amber-400';
  } else if (verdict.includes('Generated') || verdict.includes('Deepfake')) {
    riskLevel = 'High Risk';
    RiskIcon = Zap;
    riskColor = 'text-red-400';
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-4" style={{ background: 'var(--background)' }}>
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
            className="flex items-center gap-2 text-muted-foreground hover:text-white text-sm mb-4 transition-all"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </motion.button>
          <h1 className="text-3xl md:text-4xl font-bold font-display text-white">Analysis Results</h1>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card-xl p-6 md:p-8"
        >
          {/* Top Section: Verdict & Confidence */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-8 mb-8 pb-8 border-b border-white/10">
            <div className="flex flex-col items-center md:items-start gap-4">
              <VerdictBadge verdict={verdict} />
              <motion.div
                whileHover={{ scale: 1.05 }}
                className={`flex items-center gap-2 px-4 py-2 rounded-full glass-strong border ${riskColor}`}
              >
                <RiskIcon className="w-4 h-4" />
                <span className="text-sm font-medium">{riskLevel}</span>
              </motion.div>
            </div>
            
            <ConfidenceGauge value={confidence} />
          </div>

          {/* Key Findings */}
          {findings.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mb-8"
            >
              <h3 className="text-lg font-bold text-white mb-4 font-display">Key Findings</h3>
              <div className="space-y-3">
                {findings.map((finding, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + idx * 0.05 }}
                    whileHover={{ scale: 1.01, x: 4 }}
                    className="flex items-start gap-3 p-4 glass rounded-xl cursor-pointer"
                  >
                    <span className={`text-lg leading-none ${finding.startsWith('✓') ? 'text-emerald-400' : finding.startsWith('✗') ? 'text-red-400' : 'text-cyan-400'}`}>
                      {finding.charAt(0)}
                    </span>
                    <span className="text-muted-foreground text-sm leading-relaxed">{finding.substring(1).trim()}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Advanced Analysis Accordion */}
          <div className="mt-8 border-t border-white/10 pt-6">
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full p-4 glass-strong rounded-xl transition-all"
            >
              <span className="font-bold text-muted-foreground">Advanced Analysis & Metadata</span>
              <motion.div
                animate={{ rotate: showAdvanced ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="w-5 h-5 text-muted-foreground" />
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
                      <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Detection Scores</h4>
                      <div className="p-4 glass rounded-xl space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground text-sm">AI Probability</span>
                          <span className="text-white font-mono">{aiProb.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-white/10 rounded-full h-1.5">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${aiProb}%` }}
                            transition={{ duration: 0.8 }}
                            className="bg-gradient-to-r from-orange-500 to-red-500 h-1.5 rounded-full"
                          />
                        </div>
                        
                        <div className="flex justify-between items-center pt-2">
                          <span className="text-muted-foreground text-sm">Deepfake Probability</span>
                          <span className="text-white font-mono">{deepfakeProb.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-white/10 rounded-full h-1.5">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${deepfakeProb}%` }}
                            transition={{ duration: 0.8, delay: 0.2 }}
                            className="bg-gradient-to-r from-red-500 to-rose-500 h-1.5 rounded-full"
                          />
                        </div>
                      </div>
                    </div>
                    
                    {/* Metadata */}
                    <div className="space-y-4">
                      <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">File Metadata</h4>
                      <div className="p-4 glass rounded-xl space-y-2">
                        {Object.entries(metadata).length > 0 ? (
                          Object.entries(metadata).map(([key, val]) => (
                            <div key={key} className="flex justify-between items-start gap-4">
                              <span className="text-muted-foreground text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                              <span className="text-white text-sm text-right font-mono truncate max-w-[200px]">{String(val)}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-muted-foreground text-sm">No advanced metadata available.</div>
                        )}
                      </div>
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
