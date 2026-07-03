import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ConfidenceGauge from '../components/ConfidenceGauge';
import VerdictBadge from '../components/VerdictBadge';
import { ChevronDown, AlertTriangle, ShieldCheck, ShieldAlert, Zap } from 'lucide-react';

const Results = () => {
  const location = useLocation();
  const { result, type } = location.state || {};
  const [showAdvanced, setShowAdvanced] = useState(false);

  if (!result) {
    return (
      <div className="min-h-screen bg-[#030912] flex items-center justify-center">
        <div className="text-gray-500">No results to display</div>
      </div>
    );
  }

  // Handle both new and legacy API formats
  const verdict = result.verdict || result.result || 'Unknown';
  const confidence = result.confidence || result.authenticity_score || 0;
  const aiProb = result.ai_probability || result.ai_detection_score || 0;
  const deepfakeProb = result.deepfake_probability || 0;
  const findings = result.key_findings || result.reasons || result.issues || [];
  const metadata = result.metadata_summary || {};
  
  // Determine risk level based on verdict
  let riskLevel = 'Unknown Risk';
  let RiskIcon = ShieldAlert;
  let riskColor = 'text-gray-400';
  
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
    <div className="min-h-screen bg-[#030912] pt-24 pb-16 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-white font-['Space_Grotesk'] mb-8">Analysis Results</h1>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/2 border border-white/6 rounded-3xl p-6 md:p-8"
        >
          {/* Top Section: Verdict & Confidence */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-8 mb-8 pb-8 border-b border-white/6">
            <div className="flex flex-col items-center md:items-start gap-4">
              <VerdictBadge verdict={verdict} />
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/3 border border-white/6 ${riskColor}`}>
                <RiskIcon className="w-4 h-4" />
                <span className="text-sm font-medium">{riskLevel}</span>
              </div>
            </div>
            
            <ConfidenceGauge value={confidence} />
          </div>

          {/* Key Findings (User Friendly) */}
          {findings.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-bold text-white mb-4">Key Findings</h3>
              <div className="space-y-3">
                {findings.map((finding, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-4 bg-white/3 border border-white/5 rounded-xl">
                    <span className={`text-lg leading-none ${finding.startsWith('✓') ? 'text-emerald-400' : finding.startsWith('✗') ? 'text-red-400' : 'text-cyan-400'}`}>
                      {finding.charAt(0)}
                    </span>
                    <span className="text-gray-300 text-sm leading-relaxed">{finding.substring(1).trim()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}



          {/* Advanced Analysis Accordion */}
          <div className="mt-8 border-t border-white/6 pt-6">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center justify-between w-full p-4 bg-white/3 border border-white/6 rounded-xl hover:bg-white/5 transition"
            >
              <span className="font-bold text-gray-300">Advanced Analysis & Metadata</span>
              <ChevronDown className={`w-5 h-5 text-gray-500 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
            </button>
            
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
                      <h4 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Detection Scores</h4>
                      <div className="p-4 bg-black/20 rounded-xl space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">AI Probability</span>
                          <span className="text-white font-mono">{aiProb.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-white/10 rounded-full h-1.5">
                          <div className="bg-orange-500 h-1.5 rounded-full" style={{ width: `${aiProb}%` }}></div>
                        </div>
                        
                        <div className="flex justify-between items-center pt-2">
                          <span className="text-gray-400 text-sm">Deepfake Probability</span>
                          <span className="text-white font-mono">{deepfakeProb.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-white/10 rounded-full h-1.5">
                          <div className="bg-red-500 h-1.5 rounded-full" style={{ width: `${deepfakeProb}%` }}></div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Metadata */}
                    <div className="space-y-4">
                      <h4 className="text-sm font-bold text-gray-400 uppercase tracking-wider">File Metadata</h4>
                      <div className="p-4 bg-black/20 rounded-xl space-y-2">
                        {Object.entries(metadata).length > 0 ? (
                          Object.entries(metadata).map(([key, val]) => (
                            <div key={key} className="flex justify-between items-start gap-4">
                              <span className="text-gray-400 text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                              <span className="text-white text-sm text-right font-mono truncate max-w-[200px]">{String(val)}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-gray-500 text-sm">No advanced metadata available.</div>
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
