import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, X, Image as ImageIcon, Play, Pause, Download, Trash2, CheckCircle, Clock, Activity, BarChart3, FileText, Share2, AlertCircle } from 'lucide-react';
import UploadZone from '../components/ui/UploadZone';
import VerdictBadge from '../components/VerdictBadge';

/**
 * Batch Mode
 * 
 * Allows multiple image uploads with queue management and batch analysis
 */
const BatchMode = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [paused, setPaused] = useState(false);
  const [completed, setCompleted] = useState(0);
  const [failed, setFailed] = useState(0);

  const handleFilesUpload = (uploadedFiles) => {
    const newFiles = uploadedFiles.map((file, index) => ({
      id: `file-${Date.now()}-${index}`,
      file,
      preview: URL.createObjectURL(file),
      status: 'pending',
      result: null,
      progress: 0
    }));
    setFiles(prev => [...prev, ...newFiles]);
  };

  const startAnalysis = async () => {
    if (files.length === 0) return;
    
    setAnalyzing(true);
    setPaused(false);
    
    for (let i = 0; i < files.length; i++) {
      if (paused) break;
      
      setFiles(prev => {
        const updated = [...prev];
        updated[i] = { ...updated[i], status: 'analyzing', progress: 0 };
        return updated;
      });

      // Simulate analysis progress
      for (let progress = 0; progress <= 100; progress += 10) {
        if (paused) break;
        await new Promise(resolve => setTimeout(resolve, 200));
        setFiles(prev => {
          const updated = [...prev];
          updated[i] = { ...updated[i], progress };
          return updated;
        });
      }

      if (!paused) {
        const result = {
          verdict: Math.random() > 0.5 ? 'Authentic' : 'AI Generated',
          confidence: 85 + Math.random() * 10,
          aiProbability: Math.random() * 30,
          truthScore: 70 + Math.random() * 25,
          processingTime: 1 + Math.random()
        };

        setFiles(prev => {
          const updated = [...prev];
          updated[i] = { ...updated[i], status: 'completed', result, progress: 100 };
          return updated;
        });

        setCompleted(prev => prev + 1);
      }
    }

    setAnalyzing(false);
  };

  const pauseAnalysis = () => {
    setPaused(true);
    setAnalyzing(false);
  };

  const resumeAnalysis = () => {
    setPaused(false);
    const currentIndex = files.findIndex(f => f.status === 'analyzing' || f.status === 'pending');
    if (currentIndex !== -1) {
      startAnalysis();
    }
  };

  const removeFile = (id) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const clearAll = () => {
    setFiles([]);
    setCompleted(0);
    setFailed(0);
    setPaused(false);
    setAnalyzing(false);
  };

  const exportResults = (format) => {
    // Simulate export
    console.log(`Exporting results as ${format}`);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-text-muted" />;
      case 'analyzing':
        return <Activity className="w-4 h-4 text-accent animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-success" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-danger" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'text-text-muted';
      case 'analyzing':
        return 'text-accent';
      case 'completed':
        return 'text-success';
      case 'failed':
        return 'text-danger';
      default:
        return 'text-text-muted';
    }
  };

  const statistics = {
    total: files.length,
    completed,
    failed,
    pending: files.filter(f => f.status === 'pending').length,
    analyzing: files.filter(f => f.status === 'analyzing').length,
    avgConfidence: files.filter(f => f.result).length > 0
      ? files.filter(f => f.result).reduce((acc, f) => acc + f.result.confidence, 0) / files.filter(f => f.result).length
      : 0,
    aiGenerated: files.filter(f => f.result?.verdict === 'AI Generated').length,
    authentic: files.filter(f => f.result?.verdict === 'Authentic').length
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
          <h1 className="text-3xl md:text-4xl font-bold font-display text-text-primary">Batch Mode</h1>
          <p className="text-text-secondary mt-2">Upload multiple images for batch authenticity analysis</p>
        </motion.div>

        {/* Upload Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <UploadZone onFileSelect={handleFilesUpload} multiple />
        </motion.div>

        {/* Statistics */}
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-8"
          >
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Total</p>
              <p className="text-2xl font-bold text-text-primary">{statistics.total}</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Completed</p>
              <p className="text-2xl font-bold text-success">{statistics.completed}</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Pending</p>
              <p className="text-2xl font-bold text-text-muted">{statistics.pending}</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Failed</p>
              <p className="text-2xl font-bold text-danger">{statistics.failed}</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Authentic</p>
              <p className="text-2xl font-bold text-success">{statistics.authentic}</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">AI Generated</p>
              <p className="text-2xl font-bold text-danger">{statistics.aiGenerated}</p>
            </div>
            <div className="p-4 bg-glass rounded-xl border border-card/50">
              <p className="text-text-secondary text-xs mb-1">Avg Confidence</p>
              <p className="text-2xl font-bold text-accent">{statistics.avgConfidence.toFixed(1)}%</p>
            </div>
          </motion.div>
        )}

        {/* Control Buttons */}
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-wrap gap-4 mb-8"
          >
            {!analyzing && !paused && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={startAnalysis}
                disabled={files.length === 0}
                className="px-6 py-3 bg-accent text-white rounded-xl font-semibold shadow-glow flex items-center gap-2 disabled:opacity-50"
              >
                <Play className="w-4 h-4" /> Start Analysis
              </motion.button>
            )}
            {analyzing && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={pauseAnalysis}
                className="px-6 py-3 bg-warning text-white rounded-xl font-semibold shadow-glow flex items-center gap-2"
              >
                <Pause className="w-4 h-4" /> Pause
              </motion.button>
            )}
            {paused && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={resumeAnalysis}
                className="px-6 py-3 bg-success text-white rounded-xl font-semibold shadow-glow flex items-center gap-2"
              >
                <Play className="w-4 h-4" /> Resume
              </motion.button>
            )}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={clearAll}
              className="px-6 py-3 bg-glass text-text-primary rounded-xl font-semibold border border-card/50 flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" /> Clear All
            </motion.button>
          </motion.div>
        )}

        {/* File Queue */}
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-card rounded-2xl p-6 border border-card/50 shadow-glow"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-text-primary">Analysis Queue</h2>
              <div className="flex items-center gap-2">
                <span className="text-text-secondary text-sm">{completed}/{files.length} completed</span>
              </div>
            </div>

            <div className="space-y-3">
              {files.map((file, index) => (
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + index * 0.05 }}
                  className="flex items-center gap-4 p-4 bg-glass rounded-xl border border-card/50"
                >
                  {/* Thumbnail */}
                  <div className="w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
                    <img src={file.preview} alt={file.file.name} className="w-full h-full object-cover" />
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium text-text-primary truncate">{file.file.name}</p>
                      {getStatusIcon(file.status)}
                    </div>
                    <p className="text-text-secondary text-sm">{(file.file.size / 1024).toFixed(1)} KB</p>
                    {file.status === 'analyzing' && (
                      <div className="mt-2 w-full h-1 bg-card/50 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${file.progress}%` }}
                          className="h-full bg-accent rounded-full"
                        />
                      </div>
                    )}
                  </div>

                  {/* Result */}
                  {file.result && (
                    <div className="flex items-center gap-4">
                      <VerdictBadge verdict={file.result.verdict} />
                      <div className="text-right">
                        <p className="text-text-primary font-mono text-sm">{file.result.confidence.toFixed(1)}%</p>
                        <p className="text-text-secondary text-xs">confidence</p>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => removeFile(file.id)}
                    disabled={file.status === 'analyzing'}
                    className="p-2 rounded-lg bg-glass hover:bg-danger/10 text-text-secondary hover:text-danger transition-colors disabled:opacity-50 border border-card/50"
                  >
                    <X className="w-4 h-4" />
                  </motion.button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Export Section */}
        {completed > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-card rounded-2xl p-6 border border-card/50 shadow-glow mt-8"
          >
            <h2 className="text-xl font-bold text-text-primary mb-6">Export Results</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => exportResults('csv')}
                className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
              >
                <BarChart3 className="w-5 h-5 text-accent" />
                <span className="text-xs text-text-secondary">CSV Data</span>
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => exportResults('json')}
                className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
              >
                <Download className="w-5 h-5 text-accent" />
                <span className="text-xs text-text-secondary">JSON Export</span>
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => exportResults('share')}
                className="flex flex-col items-center gap-2 p-4 bg-glass rounded-xl border border-card/50 hover:border-accent/50 transition-all"
              >
                <Share2 className="w-5 h-5 text-accent" />
                <span className="text-xs text-text-secondary">Share Link</span>
              </motion.button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default BatchMode;
