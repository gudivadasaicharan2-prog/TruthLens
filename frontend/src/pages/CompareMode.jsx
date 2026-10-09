import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, X, Image as ImageIcon, Sparkles, Eye, Shield, Zap, AlertTriangle, CheckCircle, ChevronDown, ChevronUp, Download, Share2 } from 'lucide-react';
import UploadZone from '../components/ui/UploadZone';
import ImageZoom from '../components/ui/ImageZoom';
import VerdictBadge from '../components/VerdictBadge';

/**
 * Compare Mode
 * 
 * Allows side-by-side comparison of two images with detailed analysis
 */
const CompareMode = () => {
  const navigate = useNavigate();
  const [image1, setImage1] = useState(null);
  const [image2, setImage2] = useState(null);
  const [results1, setResults1] = useState(null);
  const [results2, setResults2] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('original');
  const [expandedSection, setExpandedSection] = useState('comparison');

  const handleImage1Upload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => setImage1(e.target.result);
    reader.readAsDataURL(file);
  };

  const handleImage2Upload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => setImage2(e.target.result);
    reader.readAsDataURL(file);
  };

  const handleCompare = async () => {
    if (!image1 || !image2) return;
    
    setAnalyzing(true);
    // Simulate analysis
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setResults1({
      verdict: 'Authentic',
      confidence: 94.5,
      aiProbability: 5.5,
      deepfakeProbability: 2.1,
      truthScore: 92,
      processingTime: 1.2,
      heatmap_url: image1,
      overlay_url: image1
    });

    setResults2({
      verdict: 'AI Generated',
      confidence: 87.3,
      aiProbability: 87.3,
      deepfakeProbability: 65.2,
      truthScore: 35,
      processingTime: 1.1,
      heatmap_url: image2,
      overlay_url: image2
    });

    setAnalyzing(false);
  };

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const getRiskColor = (verdict) => {
    if (verdict.includes('Authentic')) return 'text-success';
    if (verdict.includes('Suspicious')) return 'text-warning';
    return 'text-danger';
  };

  const getRiskIcon = (verdict) => {
    if (verdict.includes('Authentic')) return CheckCircle;
    if (verdict.includes('Suspicious')) return AlertTriangle;
    return Zap;
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
          <h1 className="text-3xl md:text-4xl font-bold font-display text-text-primary">Compare Mode</h1>
          <p className="text-text-secondary mt-2">Upload two images to compare their authenticity analysis side-by-side</p>
        </motion.div>

        {/* Upload Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8"
        >
          {/* Image 1 Upload */}
          <div className="bg-card rounded-2xl p-6 border border-card/50 shadow-glow">
            <h3 className="text-lg font-bold text-text-primary mb-4">Image 1</h3>
            {image1 ? (
              <div className="relative">
                <img src={image1} alt="Image 1" className="w-full aspect-square object-cover rounded-xl" />
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setImage1(null)}
                  className="absolute top-2 right-2 p-2 bg-danger/80 rounded-lg text-white"
                >
                  <X className="w-4 h-4" />
                </motion.button>
              </div>
            ) : (
              <UploadZone onFileSelect={handleImage1Upload} />
            )}
          </div>

          {/* Image 2 Upload */}
          <div className="bg-card rounded-2xl p-6 border border-card/50 shadow-glow">
            <h3 className="text-lg font-bold text-text-primary mb-4">Image 2</h3>
            {image2 ? (
              <div className="relative">
                <img src={image2} alt="Image 2" className="w-full aspect-square object-cover rounded-xl" />
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setImage2(null)}
                  className="absolute top-2 right-2 p-2 bg-danger/80 rounded-lg text-white"
                >
                  <X className="w-4 h-4" />
                </motion.button>
              </div>
            ) : (
              <UploadZone onFileSelect={handleImage2Upload} />
            )}
          </div>
        </motion.div>

        {/* Compare Button */}
        {image1 && image2 && !analyzing && !results1 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex justify-center mb-8"
          >
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleCompare}
              className="px-8 py-4 bg-accent text-white rounded-2xl font-bold text-lg shadow-glow flex items-center gap-2"
            >
              <Sparkles className="w-5 h-5" />
              Compare Images
            </motion.button>
          </motion.div>
        )}

        {/* Analyzing State */}
        {analyzing && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-card rounded-2xl p-8 border border-card/50 shadow-glow mb-8 text-center"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="w-16 h-16 mx-auto mb-4 border-4 border-accent/30 border-t-accent rounded-full"
            />
            <p className="text-text-primary font-medium">Analyzing images...</p>
            <p className="text-text-secondary text-sm">This may take a few seconds</p>
          </motion.div>
        )}

        {/* Comparison Results */}
        {results1 && results2 && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              {/* Comparison Summary */}
              <div className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow mb-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-text-primary">Comparison Summary</h2>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => toggleSection('comparison')}
                    className="p-2 rounded-lg bg-glass hover:bg-card/50 transition-all"
                  >
                    {expandedSection === 'comparison' ? <ChevronUp className="w-5 h-5 text-text-secondary" /> : <ChevronDown className="w-5 h-5 text-text-secondary" />}
                  </motion.button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Image 1 Results */}
                  <div className="p-6 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                        <ImageIcon className="w-5 h-5 text-accent" />
                      </div>
                      <div>
                        <p className="font-medium text-text-primary">Image 1</p>
                        <VerdictBadge verdict={results1.verdict} />
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Confidence</span>
                        <span className="text-text-primary font-mono">{results1.confidence.toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">AI Probability</span>
                        <span className="text-text-primary font-mono">{results1.aiProbability.toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Truth Score</span>
                        <span className="text-text-primary font-mono">{results1.truthScore}/100</span>
                      </div>
                    </div>
                  </div>

                  {/* Image 2 Results */}
                  <div className="p-6 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                        <ImageIcon className="w-5 h-5 text-accent" />
                      </div>
                      <div>
                        <p className="font-medium text-text-primary">Image 2</p>
                        <VerdictBadge verdict={results2.verdict} />
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Confidence</span>
                        <span className="text-text-primary font-mono">{results2.confidence.toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">AI Probability</span>
                        <span className="text-text-primary font-mono">{results2.aiProbability.toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Truth Score</span>
                        <span className="text-text-primary font-mono">{results2.truthScore}/100</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Key Differences */}
                <div className="mt-6 p-4 bg-glass-dark rounded-xl border border-card/50">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-5 h-5 text-warning" />
                    <h3 className="font-semibold text-text-primary">Key Differences</h3>
                  </div>
                  <ul className="space-y-2 text-sm text-text-secondary">
                    <li className="flex items-start gap-2">
                      <span className="text-warning mt-1">•</span>
                      <span>Image 2 shows significantly higher AI probability ({(results2.aiProbability - results1.aiProbability).toFixed(1)}% difference)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-warning mt-1">•</span>
                      <span>Truth score difference: {(results1.truthScore - results2.truthScore).toFixed(1)} points</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-success mt-1">•</span>
                      <span>Image 1 is classified as authentic while Image 2 is AI-generated</span>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Visual Comparison */}
              <div className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow mb-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-text-primary">Visual Comparison</h2>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => toggleSection('visual')}
                    className="p-2 rounded-lg bg-glass hover:bg-card/50 transition-all"
                  >
                    {expandedSection === 'visual' ? <ChevronUp className="w-5 h-5 text-text-secondary" /> : <ChevronDown className="w-5 h-5 text-text-secondary" />}
                  </motion.button>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                  {['original', 'heatmap', 'overlay'].map((tab) => (
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

                {/* Side-by-side Images */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="aspect-square bg-card/50 rounded-xl overflow-hidden border border-card/50">
                    <ImageZoom src={activeTab === 'original' ? image1 : results1[`${activeTab}_url`]} alt="Image 1" className="w-full h-full object-cover" />
                  </div>
                  <div className="aspect-square bg-card/50 rounded-xl overflow-hidden border border-card/50">
                    <ImageZoom src={activeTab === 'original' ? image2 : results2[`${activeTab}_url`]} alt="Image 2" className="w-full h-full object-cover" />
                  </div>
                </div>
              </div>

              {/* Export Options */}
              <div className="bg-card rounded-2xl p-6 md:p-8 border border-card/50 shadow-glow">
                <h2 className="text-xl font-bold text-text-primary mb-6">Export Comparison</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
                  >
                    <ImageIcon className="w-5 h-5 text-accent" />
                    <span className="text-xs text-text-secondary">Download Images</span>
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
                  >
                    <Share2 className="w-5 h-5 text-accent" />
                    <span className="text-xs text-text-secondary">Share Link</span>
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => {
                      setImage1(null);
                      setImage2(null);
                      setResults1(null);
                      setResults2(null);
                    }}
                    className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-danger/50 transition-all"
                  >
                    <X className="w-5 h-5 text-danger" />
                    <span className="text-xs text-text-secondary">Clear All</span>
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
};

export default CompareMode;
