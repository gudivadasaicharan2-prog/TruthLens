import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Download, Share2, Eye, ExternalLink, Copy, Check, X, Loader2, Image as ImageIcon, Code, Calendar, User, Shield, AlertTriangle } from 'lucide-react';

/**
 * Professional Report Center
 * 
 * Allows previewing, opening, downloading, and sharing analysis reports
 */
const ReportCenter = ({ result, onClose }) => {
  const [activeTab, setActiveTab] = useState('preview');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [shareLink, setShareLink] = useState(`https://truthlens.app/analysis/${result?.analysis_id || 'demo'}`);

  const handleDownload = async (format) => {
    setLoading(true);
    // Simulate download
    await new Promise(resolve => setTimeout(resolve, 1500));
    setLoading(false);
    console.log(`Downloading report as ${format}`);
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(shareLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy link');
    }
  };

  const handleOpen = () => {
    window.open(shareLink, '_blank');
  };

  const reportFormats = [
    { id: 'pdf', name: 'PDF Report', icon: FileText, description: 'Comprehensive analysis document' },
    { id: 'json', name: 'JSON Data', icon: Code, description: 'Raw analysis data' },
    { id: 'images', name: 'Image Pack', icon: ImageIcon, description: 'Original, heatmap, and overlay' },
  ];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-4xl bg-card rounded-2xl border border-card/50 shadow-glow overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-card/50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                <FileText className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-text-primary">Report Center</h2>
                <p className="text-text-secondary text-sm">Analysis ID: {result?.analysis_id || 'N/A'}</p>
              </div>
            </div>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={onClose}
              className="p-2 rounded-lg bg-glass hover:bg-card/50 text-text-secondary transition-colors"
            >
              <X className="w-5 h-5" />
            </motion.button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-card/50">
            {['preview', 'download', 'share'].map((tab) => (
              <motion.button
                key={tab}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 px-6 py-4 text-sm font-medium transition-all ${
                  activeTab === tab
                    ? 'text-accent border-b-2 border-accent bg-accent/5'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </motion.button>
            ))}
          </div>

          {/* Content */}
          <div className="p-6">
            <AnimatePresence mode="wait">
              {activeTab === 'preview' && (
                <motion.div
                  key="preview"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <div className="mb-6">
                    <h3 className="text-lg font-bold text-text-primary mb-4">Report Preview</h3>
                    <div className="bg-glass rounded-xl border border-card/50 p-6">
                      <div className="grid grid-cols-2 gap-4 mb-6">
                        <div className="flex items-center gap-3">
                          <Calendar className="w-5 h-5 text-accent" />
                          <div>
                            <p className="text-text-secondary text-xs">Date</p>
                            <p className="text-text-primary text-sm">{new Date().toLocaleDateString()}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <User className="w-5 h-5 text-accent" />
                          <div>
                            <p className="text-text-secondary text-xs">Analyst</p>
                            <p className="text-text-primary text-sm">TruthLens AI</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Shield className="w-5 h-5 text-accent" />
                          <div>
                            <p className="text-text-secondary text-xs">Verdict</p>
                            <p className="text-text-primary text-sm">{result?.verdict || 'Authentic'}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <AlertTriangle className="w-5 h-5 text-accent" />
                          <div>
                            <p className="text-text-secondary text-xs">Confidence</p>
                            <p className="text-text-primary text-sm">{result?.confidence?.toFixed(1) || '94.5'}%</p>
                          </div>
                        </div>
                      </div>

                      <div className="border-t border-card/50 pt-4">
                        <h4 className="font-semibold text-text-primary mb-2">Executive Summary</h4>
                        <p className="text-text-secondary text-sm leading-relaxed">
                          This analysis was performed using the TruthLens AI detection system, which employs multiple deep learning models to assess image authenticity. The result indicates a {result?.verdict?.toLowerCase() || 'authentic'} classification with high confidence.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleOpen}
                      className="flex-1 px-4 py-3 bg-accent text-white rounded-xl font-semibold shadow-glow flex items-center justify-center gap-2"
                    >
                      <Eye className="w-4 h-4" /> Open Full Report
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setActiveTab('download')}
                      className="flex-1 px-4 py-3 bg-glass text-text-primary rounded-xl font-semibold border border-card/50 flex items-center justify-center gap-2"
                    >
                      <Download className="w-4 h-4" /> Download
                    </motion.button>
                  </div>
                </motion.div>
              )}

              {activeTab === 'download' && (
                <motion.div
                  key="download"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <h3 className="text-lg font-bold text-text-primary mb-4">Download Report</h3>
                  <div className="space-y-3">
                    {reportFormats.map((format) => {
                      const Icon = format.icon;
                      return (
                        <motion.div
                          key={format.id}
                          whileHover={{ scale: 1.01 }}
                          className="p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-12 h-12 rounded-lg bg-accent/20 flex items-center justify-center">
                                <Icon className="w-6 h-6 text-accent" />
                              </div>
                              <div>
                                <p className="font-semibold text-text-primary">{format.name}</p>
                                <p className="text-text-secondary text-sm">{format.description}</p>
                              </div>
                            </div>
                            <motion.button
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.9 }}
                              onClick={() => handleDownload(format.id)}
                              disabled={loading}
                              className="p-3 bg-accent/10 rounded-lg text-accent hover:bg-accent/20 transition-colors disabled:opacity-50"
                            >
                              {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                              ) : (
                                <Download className="w-5 h-5" />
                              )}
                            </motion.button>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </motion.div>
              )}

              {activeTab === 'share' && (
                <motion.div
                  key="share"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <h3 className="text-lg font-bold text-text-primary mb-4">Share Report</h3>
                  
                  <div className="mb-6">
                    <label className="block text-text-secondary text-sm mb-2">Share Link</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={shareLink}
                        readOnly
                        className="flex-1 px-4 py-3 bg-glass-dark rounded-xl text-text-primary border border-card/50 text-sm"
                      />
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleShare}
                        className="px-4 py-3 bg-accent text-white rounded-xl font-semibold shadow-glow flex items-center gap-2"
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        {copied ? 'Copied!' : 'Copy'}
                      </motion.button>
                    </div>
                  </div>

                  <div className="mb-6">
                    <label className="block text-text-secondary text-sm mb-2">Share Options</label>
                    <div className="grid grid-cols-2 gap-3">
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleOpen}
                        className="p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all flex items-center gap-3"
                      >
                        <ExternalLink className="w-5 h-5 text-accent" />
                        <span className="text-text-primary text-sm">Open in Browser</span>
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all flex items-center gap-3"
                      >
                        <Share2 className="w-5 h-5 text-accent" />
                        <span className="text-text-primary text-sm">Email Report</span>
                      </motion.button>
                    </div>
                  </div>

                  <div className="p-4 bg-glass-dark rounded-xl border border-card/50">
                    <div className="flex items-start gap-3">
                      <Shield className="w-5 h-5 text-warning mt-0.5" />
                      <div>
                        <p className="font-semibold text-text-primary mb-1">Privacy Notice</p>
                        <p className="text-text-secondary text-sm">
                          Shared reports are accessible via a unique link. You can revoke access at any time from your account settings.
                        </p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-card/50 bg-card/30 flex justify-end">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onClose}
              className="px-6 py-2 bg-glass text-text-primary rounded-xl font-medium border border-card/50 hover:bg-card/50 transition-all"
            >
              Close
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ReportCenter;
