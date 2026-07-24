import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Image as ImageIcon, Video, Upload, X,
  ArrowRight, Sparkles, FileText, CheckCircle2,
  Shield, AlertTriangle, Info, Download, Eye,
  Brain, Zap, FileText as FileIcon, BarChart3, Loader2
} from 'lucide-react';
import { analyzeImage, analyzeVideo, getErrorMessage } from '../services/api';

/* ── Helpers ── */
const fmt = (val) => {
  const n = parseFloat(val);
  if (isNaN(n) || !isFinite(n)) return '0';
  return n <= 1.0 ? Math.round(n * 100).toString() : Math.round(n).toString();
};

const TABS = [
  { id: 'image', icon: ImageIcon, label: 'Image', color: 'cyan', gradient: 'from-cyan-500 to-blue-600' },
  { id: 'video', icon: Video, label: 'Video', color: 'purple', gradient: 'from-purple-500 to-pink-600' },
];

const STEPS = [
  { label: 'Upload', icon: Upload },
  { label: 'Metadata', icon: FileText },
  { label: 'AI Analysis', icon: Brain },
  { label: 'Forensic', icon: Shield },
  { label: 'GradCAM', icon: Eye },
  { label: 'Report', icon: FileIcon },
  { label: 'Result', icon: CheckCircle2 },
];

const VERDICT_CONFIG = {
  'Authentic': { color: 'text-green-400', border: 'border-green-500/40', bg: 'bg-green-500/8', icon: '✅', ring: 'ring-green-500/20' },
  'Likely Authentic': { color: 'text-emerald-400', border: 'border-emerald-500/40', bg: 'bg-emerald-500/8', icon: '✅', ring: 'ring-emerald-500/20' },
  'Suspicious': { color: 'text-amber-400', border: 'border-amber-500/40', bg: 'bg-amber-500/8', icon: '⚠️', ring: 'ring-amber-500/20' },
  'Likely AI Generated': { color: 'text-orange-400', border: 'border-orange-500/40', bg: 'bg-orange-500/8', icon: '🤖', ring: 'ring-orange-500/20' },
  'AI Generated': { color: 'text-red-400', border: 'border-red-500/40', bg: 'bg-red-500/8', icon: '❌', ring: 'ring-red-500/20' },
  'Deepfake': { color: 'text-red-400', border: 'border-red-500/40', bg: 'bg-red-500/8', icon: '🎭', ring: 'ring-red-500/20' },
  'Manipulated': { color: 'text-rose-400', border: 'border-rose-500/40', bg: 'bg-rose-500/8', icon: '✂️', ring: 'ring-rose-500/20' },
};

/* ── Progress Stepper ── */
const Stepper = ({ step }) => (
  <div className="flex items-center justify-center gap-2 mb-12">
    {STEPS.map((s, i) => (
      <div key={s.label} className="flex items-center">
        <div className={`flex flex-col items-center gap-2 transition-all ${i <= step ? 'opacity-100' : 'opacity-30'}`}>
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: i === step ? [1, 1.1, 1] : 1 }}
            transition={{ duration: 0.3 }}
            className={`w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold transition-all ${i < step ? 'bg-brand text-white ring-glow' : i === step ? 'bg-brand/20 border-2 border-brand text-brand animate-pulse-slow' : 'glass text-muted-foreground'
              }`}
          >
            {i < step ? '✓' : <s.icon className="w-5 h-5" />}
          </motion.div>
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground hidden md:block">{s.label}</span>
        </div>
        {i < STEPS.length - 1 && (
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: i < step ? '40px' : '40px' }}
            className={`w-8 md:w-12 h-0.5 mx-1 transition-all ${i < step ? 'bg-brand' : 'bg-white/10'}`} 
          />
        )}
      </div>
    ))}
  </div>
);



/* ── Result Card ── */
const ResultCard = ({ result, onReset, imagePreview }) => {
  if (!result) return null;

  const verdict = result.verdict || result.result || 'Unknown';
  const confidence = fmt(result.confidence ?? result.authenticity_score);
  const keyFindings = result.key_findings || [];
  const moduleContributions = result.module_contributions || {};
  const explanation = result.explanation || {};
  const heatmapPath = result.heatmap_path;
  const overlayPath = result.overlay_path;
  const reportPath = result.report_path;

  const metaSummary = result.metadata_summary || null;
  const cfg = VERDICT_CONFIG[verdict] || {
    color: 'text-cyan-400', border: 'border-cyan-500/40',
    bg: 'bg-cyan-500/8', icon: '🔍', ring: 'ring-cyan-500/20'
  };

  const aiProb = Math.round(parseFloat(result.ai_probability ?? result.ai_detection_score ?? 0));
  const deepfakeProb = Math.round(parseFloat(result.deepfake_probability ?? 0));
  const confNum = parseInt(confidence, 10);

  const getApiUrl = (path) => {
    if (!path) return null;
    const baseUrl = import.meta.env.VITE_API_URL || 'https://truthlens-htjy.onrender.com';
    return path.startsWith('http') ? path : `${baseUrl.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="w-full max-w-3xl mx-auto space-y-6"
    >
      {/* ── Main Verdict Card ── */}
      <div className={`${cfg.bg} ${cfg.border} border rounded-3xl p-8 ring-1 ${cfg.ring} glass-card-xl`}>
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-6">
          <div className="flex items-center gap-4">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="text-6xl"
            >
              {cfg.icon}
            </motion.div>
            <div>
              <p className="text-muted-foreground text-xs uppercase tracking-widest mb-1">Verdict</p>
              <p className={`text-3xl font-bold font-display ${cfg.color}`}>{verdict}</p>
            </div>
          </div>
          <div className="text-center md:text-right">
            <p className="text-muted-foreground text-xs uppercase tracking-widest mb-1">Confidence</p>
            <p className="text-4xl font-bold text-white font-display">{confidence}%</p>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="h-3 bg-black/30 rounded-full overflow-hidden mb-6">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${confidence}%` }}
            transition={{ duration: 1.6, ease: 'easeOut' }}
            className={`h-full rounded-full bg-gradient-to-r ${confNum >= 80 ? 'from-green-500 to-emerald-400' :
                confNum >= 50 ? 'from-amber-500 to-yellow-400' :
                  'from-red-500 to-orange-400'
              }`}
          />
        </div>

        {/* Metric grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="glass rounded-2xl p-4 text-center">
            <p className="text-muted-foreground text-xs uppercase tracking-wider mb-2">Authenticity</p>
            <p className={`font-bold text-2xl ${confNum >= 70 ? 'text-green-400' : confNum >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
              {confidence}%
            </p>
          </div>
          <div className="glass rounded-2xl p-4 text-center">
            <p className="text-muted-foreground text-xs uppercase tracking-wider mb-2">AI Generated</p>
            <p className={`font-bold text-2xl ${aiProb > 60 ? 'text-orange-400' : aiProb > 30 ? 'text-amber-400' : 'text-green-400'}`}>
              {aiProb}%
            </p>
          </div>
          <div className="glass rounded-2xl p-4 text-center">
            <p className="text-muted-foreground text-xs uppercase tracking-wider mb-2">Deepfake</p>
            <p className={`font-bold text-2xl ${deepfakeProb > 60 ? 'text-red-400' : deepfakeProb > 30 ? 'text-amber-400' : 'text-green-400'}`}>
              {deepfakeProb}%
            </p>
          </div>
        </div>
      </div>

      {/* ── Module Contributions ── */}
      {moduleContributions && Object.keys(moduleContributions).length > 0 && (
        <div className="glass-card p-6 rounded-3xl">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" /> Module Contributions
          </h3>
          <div className="space-y-3">
            {Object.entries(moduleContributions).map(([moduleName, data], idx) => (
              <motion.div
                key={moduleName}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="glass rounded-2xl p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium capitalize">{moduleName.replace('_', ' ')}</span>
                  <span className="text-cyan-400 text-sm font-bold">{fmt(data.contribution || 0)}%</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>Score: {fmt(data.score || 0)}</span>
                  <span>Weight: {fmt(data.weight || 0)}</span>
                </div>
                <div className="h-2 bg-black/30 rounded-full overflow-hidden mt-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${fmt(data.contribution || 0)}%` }}
                    transition={{ duration: 0.8, delay: idx * 0.1 + 0.2 }}
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* ── Explanation (Evidence) ── */}
      {(explanation.for_ai || explanation.against_ai) && (
        <div className="glass-card p-6 rounded-3xl">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4 text-cyan-400" /> Analysis Explanation
          </h3>
          
          {explanation.for_ai && explanation.for_ai.length > 0 && (
            <div className="mb-4">
              <p className="text-orange-400 text-xs font-semibold uppercase tracking-wider mb-2">Evidence For AI</p>
              <div className="space-y-2">
                {explanation.for_ai.map((evidence, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-2 text-sm text-muted-foreground"
                  >
                    <span className="text-orange-400 mt-0.5">•</span>
                    <span>{evidence}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
          
          {explanation.against_ai && explanation.against_ai.length > 0 && (
            <div>
              <p className="text-green-400 text-xs font-semibold uppercase tracking-wider mb-2">Evidence Against AI</p>
              <div className="space-y-2">
                {explanation.against_ai.map((evidence, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-2 text-sm text-muted-foreground"
                  >
                    <span className="text-green-400 mt-0.5">•</span>
                    <span>{evidence}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── GradCAM Visualizations ── */}
      {(heatmapPath || overlayPath) && (
        <div className="glass-card p-6 rounded-3xl">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <Eye className="w-4 h-4 text-cyan-400" /> GradCAM Visualization
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {imagePreview && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-2"
              >
                <p className="text-muted-foreground text-xs">Original Image</p>
                <img src={imagePreview} alt="Original" className="w-full rounded-2xl" />
              </motion.div>
            )}
            {heatmapPath && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                className="space-y-2"
              >
                <p className="text-muted-foreground text-xs">Heatmap</p>
                <img src={getApiUrl(heatmapPath)} alt="Heatmap" className="w-full rounded-2xl" />
              </motion.div>
            )}
            {overlayPath && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
                className="space-y-2"
              >
                <p className="text-muted-foreground text-xs">Overlay</p>
                <img src={getApiUrl(overlayPath)} alt="Overlay" className="w-full rounded-2xl" />
              </motion.div>
            )}
          </div>
        </div>
      )}

      {/* ── Key Findings ── */}
      {keyFindings.length > 0 && (
        <div className="glass-card p-6 rounded-3xl">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-cyan-400" /> Key Findings
          </h3>
          <div className="space-y-3">
            {keyFindings.map((f, i) => {
              const isCheck = f.trim().startsWith('✓');
              const isCross = f.trim().startsWith('✗');
              const text = f.replace(/^[✓✗]\s*/, '');
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-start gap-3 text-sm glass rounded-2xl p-4"
                >
                  <span className={`font-bold shrink-0 mt-0.5 ${isCheck ? 'text-green-400' : isCross ? 'text-red-400' : 'text-cyan-400'}`}>
                    {isCheck ? '✓' : isCross ? '✗' : '•'}
                  </span>
                  <span className="text-muted-foreground leading-relaxed">{text}</span>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Metadata Summary ── */}
      {metaSummary && Object.keys(metaSummary).filter(k => metaSummary[k] && metaSummary[k] !== 'Unknown' && k !== 'error').length > 0 && (
        <div className="glass-card p-6 rounded-3xl">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <Info className="w-4 h-4 text-cyan-400" /> Metadata Summary
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(metaSummary).map(([key, val]) => {
              if (!val || val === 'Unknown' || key === 'error') return null;
              const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
              return (
                <div key={key} className="glass rounded-2xl px-4 py-3">
                  <p className="text-muted-foreground text-xs uppercase tracking-wider mb-1">{label}</p>
                  <p className="text-white text-sm font-medium truncate">
                    {typeof val === 'boolean' ? (val ? 'Yes ✓' : 'No ✗') : String(val)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Report Download ── */}
      {reportPath && (
        <div className="glass-card p-6 rounded-3xl">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <FileIcon className="w-4 h-4 text-cyan-400" /> Analysis Report
          </h3>
          <a
            href={getApiUrl(reportPath)}
            download
            className="inline-flex items-center gap-2 px-6 py-3 bg-brand text-white rounded-2xl font-semibold ring-glow transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Download className="w-4 h-4" /> Download PDF Report
          </a>
        </div>
      )}

      {/* Reset */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onReset}
        className="w-full py-4 glass-strong text-muted-foreground hover:text-white rounded-3xl font-semibold transition-all flex items-center justify-center gap-2 group text-lg"
      >
        Analyze Another File <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
      </motion.button>
    </motion.div>
  );
};

/* ── Drop Zone ── */
const DropZone = ({ id, accept, icon: Icon, gradient, title, hint, onUpload }) => {
  const [drag, setDrag] = useState(false);
  const handleDrag = (e) => { e.preventDefault(); e.stopPropagation(); setDrag(e.type !== 'dragleave' && e.type !== 'drop'); };
  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className={`border-2 border-dashed rounded-3xl p-20 text-center transition-all cursor-pointer ${drag ? 'border-cyan-400 bg-cyan-500/5' : 'border-white/10 hover:border-white/25 glass'
        }`}
      onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag}
      onDrop={(e) => { handleDrag(e); onUpload(e); }}
      onClick={() => document.getElementById(id)?.click()}
    >
      <input type="file" accept={accept} onChange={onUpload} className="hidden" id={id} />
      <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }} className="inline-block mb-6">
        <div className={`w-24 h-24 rounded-3xl bg-gradient-to-br ${gradient} p-0.5 mx-auto ring-glow`}>
          <div className="w-full h-full rounded-3xl flex items-center justify-center" style={{ background: 'var(--background)' }}>
            <Icon className="w-12 h-12 text-white" />
          </div>
        </div>
      </motion.div>
      <p className="text-white font-semibold text-xl mb-3 font-display">{title}</p>
      <p className="text-muted-foreground text-base mb-4">Drag and drop or click to browse</p>
      <p className="text-muted-foreground/60 text-sm">{hint}</p>
    </motion.div>
  );
};

/* ── File Card (after upload) ── */
const FileCard = ({ file, icon: Icon, gradient, btnLabel, onRemove, onAnalyze, loading }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="glass-card p-6 rounded-3xl"
  >
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-4">
        <motion.div
          whileHover={{ scale: 1.05 }}
          className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center ring-glow`}
        >
          <Icon className="w-7 h-7 text-white" />
        </motion.div>
        <div>
          <p className="text-white font-medium text-base">{file.name}</p>
          <p className="text-muted-foreground text-sm">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
        </div>
      </div>
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onRemove}
        className="p-3 glass rounded-2xl transition text-muted-foreground hover:text-white"
      >
        <X className="w-5 h-5" />
      </motion.button>
    </div>
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onAnalyze}
      disabled={loading}
      className={`w-full py-4 bg-brand text-white rounded-2xl font-semibold ring-glow transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-lg`}
    >
      {loading ? (
        <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing…</>
      ) : (
        <>{btnLabel} <ArrowRight className="w-5 h-5" /></>
      )}
    </motion.button>
  </motion.div>
);

/* ═══════════════════════════════════════════
   Main Detect Page
═══════════════════════════════════════════ */
const Detect = () => {
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'image';
  const [activeTab, setActiveTab] = useState(initialTab);

  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageResult, setImageResult] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState(null);
  const [imageStep, setImageStep] = useState(0);

  const [videoFile, setVideoFile] = useState(null);
  const [videoResult, setVideoResult] = useState(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoError, setVideoError] = useState(null);
  const [videoStep, setVideoStep] = useState(0);

  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    fetch('https://truthlens-htjy.onrender.com/health')
      .then(res => res.text())
      .then(text => console.log("[Startup] Backend health check OK:", text))
      .catch(err => console.error("[Startup] Backend health check FAILED:", err));
  }, []);

  const handleTestConnection = async () => {
    const url = 'https://truthlens-htjy.onrender.com/health';
    try {
      const res = await fetch(url);
      const text = await res.text();
      console.log("[Test Connection] Response:", res.status, text);
      showToast(`Success: HTTP ${res.status}`, 'success');
    } catch (e) {
      console.error("[Test Connection] Failed:", e);
      showToast(`Error: ${e.message}`, 'error');
    }
  };

  /* ── Handlers ── */
  const handleImage = async (e) => {
    const file = e.target?.files?.[0] || e.dataTransfer?.files?.[0];
    if (!file) return;
    const valid = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
    if (!valid.includes(file.type)) { setImageError('Invalid type. Use JPG, PNG or WEBP.'); return; }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setImageResult(null); setImageError(null);
    setImageLoading(true); setImageStep(1);
    try {
      await new Promise(r => setTimeout(r, 800));
      setImageStep(2);
      await new Promise(r => setTimeout(r, 1000));
      setImageStep(3);
      await new Promise(r => setTimeout(r, 1200));
      setImageStep(4);
      await new Promise(r => setTimeout(r, 800));
      setImageStep(5);
      await new Promise(r => setTimeout(r, 600));
      setImageStep(6);
      const data = await analyzeImage(file);
      console.log("Analyze Result:", data);
      setImageResult(data); setImageStep(7);
      showToast('Analysis complete!');
    } catch (err) {
      console.log("Caught Error:", err);
      const msg = getErrorMessage(err);
      setImageError(msg); showToast(msg, 'error');
    } finally { setImageLoading(false); }
  };

  const handleVideo = async (e) => {
    const file = e.target?.files?.[0] || e.dataTransfer?.files?.[0];
    if (!file) return;

    const VALID_VIDEO_EXTS = ['mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v', '3gp'];
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    if (!VALID_VIDEO_EXTS.includes(ext)) {
      const msg = `Unsupported format: .${ext || '(none)'}. Accepted: ${VALID_VIDEO_EXTS.join(', ').toUpperCase()}.`;
      setVideoFile(file);
      setVideoError(msg);
      showToast(msg, 'error');
      return;
    }

    setVideoFile(file); setVideoResult(null); setVideoError(null);
    setVideoLoading(true); setVideoStep(1);
    try {
      await new Promise(r => setTimeout(r, 800));
      setVideoStep(2);
      await new Promise(r => setTimeout(r, 1000));
      setVideoStep(3);
      await new Promise(r => setTimeout(r, 1200));
      setVideoStep(4);
      console.log('[handleVideo] Starting upload:', file.name);
      const data = await analyzeVideo(file);
      console.log('[handleVideo] Result:', data);
      setVideoResult(data); setVideoStep(7);
      showToast('Video analysis complete!');
    } catch (err) {
      const msg = getErrorMessage(err);
      console.error('[handleVideo] Error:', msg, err);
      setVideoError(msg);
      showToast(msg, 'error');
    } finally { setVideoLoading(false); }
  };

  const resetImage = () => { setImageFile(null); setImagePreview(null); setImageResult(null); setImageError(null); setImageStep(0); };
  const resetVideo = () => { setVideoFile(null); setVideoResult(null); setVideoError(null); setVideoStep(0); };

  const isLoading = imageLoading || videoLoading;
  const curStep = activeTab === 'image' ? imageStep : videoStep;

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`fixed top-20 left-1/2 -translate-x-1/2 z-50 px-6 py-4 rounded-2xl text-sm font-medium shadow-xl glass-strong ${toast.type === 'error'
                ? 'border-red-500/30 text-red-200'
                : 'border-green-500/30 text-green-200'
              }`}
          >
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Centered Container */}
      <div className="max-w-4xl mx-auto px-4 py-16 md:py-24">

        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }} 
          animate={{ opacity: 1, y: 0 }} 
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-6xl font-bold font-display text-white mb-4">
            Content Detection
          </h1>
          <p className="text-muted-foreground text-lg md:text-xl mb-6">
            Upload an image or video file to analyze its authenticity
          </p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleTestConnection}
            className="px-6 py-3 glass-strong text-cyan-400 rounded-2xl text-sm font-semibold transition-all hover:bg-white/5"
          >
            Test Backend Connection
          </motion.button>
        </motion.div>

        {/* Tab bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex gap-2 mb-8 glass-strong p-2 rounded-3xl border border-white/10 max-w-md mx-auto"
        >
          {TABS.map(tab => (
            <motion.button
              key={tab.id}
              whileHover={{ scale: activeTab !== tab.id ? 1.02 : 1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-4 rounded-2xl font-semibold transition-all duration-200 text-sm ${activeTab === tab.id
                  ? 'bg-brand text-white ring-glow'
                  : 'text-muted-foreground hover:text-white hover:bg-white/5'
                }`}
            >
              <div className="flex items-center justify-center gap-2">
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </div>
            </motion.button>
          ))}
        </motion.div>

        {/* Stepper (only when loading) */}
        {isLoading && <Stepper step={curStep} />}

        {/* Main panel */}
        <div className="w-full">

          {/* ═══ IMAGE TAB ═══ */}
          <div className={activeTab === 'image' ? 'block' : 'hidden'}>
            <div className="space-y-6">
              {!imageFile ? (
                <DropZone id="img-upload" accept="image/*" icon={ImageIcon}
                  gradient="from-cyan-500 to-blue-600"
                  title="Upload an Image" hint="Supports: JPG, PNG, WEBP, GIF (Max 10 MB)"
                  onUpload={handleImage}
                />
              ) : (
                <>
                  {imagePreview && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="relative rounded-3xl overflow-hidden max-h-96 glass"
                    >
                      <img src={imagePreview} alt="preview" className="w-full object-cover" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                    </motion.div>
                  )}
                  <FileCard file={imageFile} icon={ImageIcon}
                    gradient="from-cyan-500 to-blue-600" btnLabel="Analyze Image"
                    loading={imageLoading} onRemove={resetImage}
                    onAnalyze={() => handleImage({ target: { files: [imageFile] } })}
                  />
                </>
              )}

              {imageError && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="p-4 glass border-red-500/30 rounded-2xl text-red-300 text-sm flex gap-2"
                >
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {imageError}
                </motion.div>
              )}

              {imageResult?.image_type === 'screenshot' && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="p-4 glass border-blue-500/20 rounded-2xl text-blue-300 text-sm flex gap-2"
                >
                  <Info className="w-4 h-4 shrink-0 mt-0.5" />
                  Screenshot detected — deepfake analysis is optimized for photos with human faces.
                </motion.div>
              )}

              <ResultCard result={imageResult} onReset={resetImage} imagePreview={imagePreview} />
            </div>
          </div>

          {/* ═══ VIDEO TAB ═══ */}
          <div className={activeTab === 'video' ? 'block' : 'hidden'}>
            <div className="space-y-6">
              {!videoFile ? (
                <DropZone id="vid-upload" accept="video/*" icon={Video}
                  gradient="from-purple-500 to-pink-600"
                  title="Upload a Video" hint="Supports: MP4, MOV, AVI, MKV (Max 100 MB)"
                  onUpload={handleVideo}
                />
              ) : (
                <FileCard file={videoFile} icon={Video}
                  gradient="from-purple-500 to-pink-600" btnLabel="Analyze Video"
                  loading={videoLoading} onRemove={resetVideo}
                  onAnalyze={() => handleVideo({ target: { files: [videoFile] } })}
                />
              )}

              {videoError && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="p-4 glass border-red-500/30 rounded-2xl text-red-300 text-sm flex gap-2"
                >
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {videoError}
                </motion.div>
              )}

              <ResultCard result={videoResult} onReset={resetVideo} />
            </div>
          </div>

        </div>

        {/* Info note */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center text-muted-foreground/60 text-sm mt-12"
        >
          Files are processed securely and not permanently stored. Analysis uses multi-layer AI forensics.
        </motion.div>
      </div>
    </div>
  );
};

export default Detect;
