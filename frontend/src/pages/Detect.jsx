import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Image as ImageIcon, Video, Mic, Upload, X,
  ArrowRight, Sparkles, FileText, CheckCircle2,
  Shield, AlertTriangle, Info
} from 'lucide-react';
import { analyzeImage, analyzeVideo, analyzeAudio, getErrorMessage } from '../services/api';

/* ── Helpers ── */
const fmt = (val) => {
  const n = parseFloat(val);
  if (isNaN(n) || !isFinite(n)) return '0';
  return n <= 1.0 ? Math.round(n * 100).toString() : Math.round(n).toString();
};

const TABS = [
  { id: 'image', icon: ImageIcon, label: '🖼️ Image', color: 'cyan',   gradient: 'from-cyan-500 to-blue-600' },
  { id: 'video', icon: Video,     label: '🎥 Video', color: 'purple', gradient: 'from-purple-500 to-pink-600' },
  { id: 'audio', icon: Mic,       label: '🔊 Audio', color: 'green',  gradient: 'from-green-500 to-emerald-600' },
];

const STEPS = [
  { label: 'Upload',     icon: Upload },
  { label: 'Processing', icon: Sparkles },
  { label: 'Analysis',   icon: FileText },
  { label: 'Result',     icon: CheckCircle2 },
];

const VERDICT_CONFIG = {
  'Authentic':           { color: 'text-green-400',   border: 'border-green-500/40',   bg: 'bg-green-500/8',   icon: '✅', ring: 'ring-green-500/20' },
  'Likely Authentic':    { color: 'text-emerald-400',  border: 'border-emerald-500/40', bg: 'bg-emerald-500/8', icon: '✅', ring: 'ring-emerald-500/20' },
  'Suspicious':          { color: 'text-amber-400',    border: 'border-amber-500/40',   bg: 'bg-amber-500/8',   icon: '⚠️', ring: 'ring-amber-500/20' },
  'Likely AI Generated': { color: 'text-orange-400',   border: 'border-orange-500/40',  bg: 'bg-orange-500/8',  icon: '🤖', ring: 'ring-orange-500/20' },
  'AI Generated':        { color: 'text-red-400',      border: 'border-red-500/40',     bg: 'bg-red-500/8',     icon: '❌', ring: 'ring-red-500/20' },
  'Deepfake':            { color: 'text-red-400',      border: 'border-red-500/40',     bg: 'bg-red-500/8',     icon: '🎭', ring: 'ring-red-500/20' },
  'Manipulated':         { color: 'text-rose-400',     border: 'border-rose-500/40',    bg: 'bg-rose-500/8',    icon: '✂️', ring: 'ring-rose-500/20' },
};

/* ── Progress Stepper ── */
const Stepper = ({ step }) => (
  <div className="flex items-center justify-center gap-0 mb-8">
    {STEPS.map((s, i) => (
      <div key={s.label} className="flex items-center">
        <div className={`flex flex-col items-center gap-1 transition-all ${i <= step ? 'opacity-100' : 'opacity-30'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
            i < step ? 'bg-cyan-500 text-white' : i === step ? 'bg-cyan-500/20 border border-cyan-500 text-cyan-400 animate-pulse' : 'bg-white/5 border border-white/10 text-gray-500'
          }`}>
            {i < step ? '✓' : <s.icon className="w-3.5 h-3.5" />}
          </div>
          <span className="text-[10px] text-gray-500 hidden sm:block">{s.label}</span>
        </div>
        {i < STEPS.length - 1 && (
          <div className={`w-12 sm:w-20 h-px mx-1 transition-all ${i < step ? 'bg-cyan-500' : 'bg-white/10'}`} />
        )}
      </div>
    ))}
  </div>
);



/* ── Result Card ── */
const ResultCard = ({ result, onReset }) => {
  if (!result) return null;

  const verdict = result.verdict || result.result || 'Unknown';
  const confidence = fmt(result.confidence ?? result.authenticity_score);
  const keyFindings = result.key_findings || [];
  const sourceLinks = (result.source_links || []).filter(
    s => s.url && !s.url.toLowerCase().includes('wikipedia.org')
  );
  const metaSummary = result.metadata_summary || null;
  const cfg = VERDICT_CONFIG[verdict] || {
    color: 'text-cyan-400', border: 'border-cyan-500/40',
    bg: 'bg-cyan-500/8', icon: '🔍', ring: 'ring-cyan-500/20'
  };

  const aiProb       = Math.round(parseFloat(result.ai_probability ?? result.ai_detection_score ?? 0));
  const deepfakeProb = Math.round(parseFloat(result.deepfake_probability ?? 0));
  const confNum      = parseInt(confidence, 10);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mt-8 space-y-4"
    >
      {/* ── Main Verdict Card ── */}
      <div className={`${cfg.bg} ${cfg.border} border rounded-2xl p-6 ring-1 ${cfg.ring}`}>
        <div className="flex items-center justify-between gap-4 mb-5">
          <div className="flex items-center gap-4">
            <span className="text-4xl">{cfg.icon}</span>
            <div>
              <p className="text-gray-400 text-xs uppercase tracking-widest mb-1">Verdict</p>
              <p className={`text-2xl font-bold font-['Space_Grotesk'] ${cfg.color}`}>{verdict}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-gray-400 text-xs uppercase tracking-widest mb-1">Confidence</p>
            <p className="text-3xl font-bold text-white font-['Space_Grotesk']">{confidence}%</p>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="h-2 bg-black/30 rounded-full overflow-hidden mb-5">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${confidence}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className={`h-full rounded-full bg-gradient-to-r ${
              confNum >= 80 ? 'from-green-500 to-emerald-400' :
              confNum >= 50 ? 'from-amber-500 to-yellow-400' :
              'from-red-500 to-orange-400'
            }`}
          />
        </div>

        {/* Metric grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-black/20 rounded-xl p-3 text-center">
            <p className="text-gray-500 text-[10px] uppercase tracking-wider mb-1">Authenticity</p>
            <p className={`font-bold text-lg ${confNum >= 70 ? 'text-green-400' : confNum >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
              {confidence}%
            </p>
          </div>
          <div className="bg-black/20 rounded-xl p-3 text-center">
            <p className="text-gray-500 text-[10px] uppercase tracking-wider mb-1">AI Generated</p>
            <p className={`font-bold text-lg ${aiProb > 60 ? 'text-orange-400' : aiProb > 30 ? 'text-amber-400' : 'text-green-400'}`}>
              {aiProb}%
            </p>
          </div>
          <div className="bg-black/20 rounded-xl p-3 text-center">
            <p className="text-gray-500 text-[10px] uppercase tracking-wider mb-1">Deepfake</p>
            <p className={`font-bold text-lg ${deepfakeProb > 60 ? 'text-red-400' : deepfakeProb > 30 ? 'text-amber-400' : 'text-green-400'}`}>
              {deepfakeProb}%
            </p>
          </div>
        </div>
      </div>

      {/* ── Key Findings ── */}
      {keyFindings.length > 0 && (
        <div className="bg-white/3 border border-white/8 rounded-2xl p-6">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-cyan-400" /> Key Findings
          </h3>
          <div className="space-y-2.5">
            {keyFindings.map((f, i) => {
              const isCheck = f.trim().startsWith('✓');
              const isCross = f.trim().startsWith('✗');
              const text = f.replace(/^[✓✗]\s*/, '');
              return (
                <div key={i} className="flex items-start gap-3 text-sm">
                  <span className={`font-bold shrink-0 mt-0.5 ${isCheck ? 'text-green-400' : isCross ? 'text-red-400' : 'text-cyan-400'}`}>
                    {isCheck ? '✓' : isCross ? '✗' : '•'}
                  </span>
                  <span className="text-gray-300 leading-relaxed">{text}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Metadata Summary ── */}
      {metaSummary && Object.keys(metaSummary).filter(k => metaSummary[k] && metaSummary[k] !== 'Unknown' && k !== 'error').length > 0 && (
        <div className="bg-white/3 border border-white/8 rounded-2xl p-6">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <Info className="w-4 h-4 text-cyan-400" /> Metadata Summary
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(metaSummary).map(([key, val]) => {
              if (!val || val === 'Unknown' || key === 'error') return null;
              const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
              return (
                <div key={key} className="bg-black/20 rounded-xl px-4 py-3">
                  <p className="text-gray-500 text-[10px] uppercase tracking-wider mb-1">{label}</p>
                  <p className="text-gray-200 text-sm font-medium truncate">
                    {typeof val === 'boolean' ? (val ? 'Yes ✓' : 'No ✗') : String(val)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Source Links (non-Wikipedia only) ── */}
      {sourceLinks.length > 0 && (
        <div className="bg-white/3 border border-white/8 rounded-2xl p-6">
          <h3 className="text-white text-sm font-semibold uppercase tracking-wider mb-4">Original Sources</h3>
          <div className="space-y-2">
            {sourceLinks.map((src, i) => (
              <a
                key={i}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-white/3 hover:bg-white/6 border border-white/5 hover:border-cyan-500/20 rounded-xl transition group"
              >
                <span className="text-gray-300 text-sm group-hover:text-cyan-400 transition truncate">• {src.name}</span>
                <span className="text-cyan-400 text-xs shrink-0 ml-3">↗ Open</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Reset */}
      <button
        onClick={onReset}
        className="w-full py-3 border border-white/10 text-gray-400 hover:text-white hover:border-cyan-500/30 rounded-2xl font-semibold transition-all flex items-center justify-center gap-2 group"
      >
        Analyze Another File <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
      </button>
    </motion.div>
  );
};

/* ── Drop Zone ── */
const DropZone = ({ id, accept, icon: Icon, gradient, title, hint, onUpload }) => {
  const [drag, setDrag] = useState(false);
  const handleDrag = (e) => { e.preventDefault(); e.stopPropagation(); setDrag(e.type !== 'dragleave' && e.type !== 'drop'); };
  return (
    <div
      className={`border-2 border-dashed rounded-3xl p-16 text-center transition-all cursor-pointer ${
        drag ? 'border-cyan-400 bg-cyan-500/5' : 'border-white/10 hover:border-white/25 bg-white/2'
      }`}
      onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag}
      onDrop={(e) => { handleDrag(e); onUpload(e); }}
      onClick={() => document.getElementById(id)?.click()}
    >
      <input type="file" accept={accept} onChange={onUpload} className="hidden" id={id} />
      <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }} className="inline-block mb-4">
        <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${gradient} p-0.5 mx-auto`}>
          <div className="w-full h-full bg-[#070f1e] rounded-2xl flex items-center justify-center">
            <Icon className="w-9 h-9 text-white" />
          </div>
        </div>
      </motion.div>
      <p className="text-white font-semibold text-lg mb-2">{title}</p>
      <p className="text-gray-500 text-sm mb-3">Drag and drop or click to browse</p>
      <p className="text-gray-600 text-xs">{hint}</p>
    </div>
  );
};

/* ── File Card (after upload) ── */
const FileCard = ({ file, icon: Icon, gradient, btnLabel, onRemove, onAnalyze, loading }) => (
  <div className="bg-white/3 border border-white/8 rounded-2xl p-5">
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-white font-medium text-sm">{file.name}</p>
          <p className="text-gray-500 text-xs">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
        </div>
      </div>
      <button onClick={onRemove} className="p-2 hover:bg-white/5 rounded-lg transition text-gray-500 hover:text-white">
        <X className="w-4 h-4" />
      </button>
    </div>
    <button
      onClick={onAnalyze}
      disabled={loading}
      className={`w-full py-3 bg-gradient-to-r ${gradient} text-white rounded-xl font-semibold hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50`}
    >
      {loading ? (
        <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Analyzing…</>
      ) : (
        <>{btnLabel} <ArrowRight className="w-4 h-4" /></>
      )}
    </button>
  </div>
);

/* ═══════════════════════════════════════════
   Main Detect Page
═══════════════════════════════════════════ */
const Detect = () => {
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'image';
  const [activeTab, setActiveTab] = useState(initialTab);

  const [imageFile, setImageFile]       = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageResult, setImageResult]   = useState(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError]     = useState(null);
  const [imageStep, setImageStep]       = useState(0);

  const [videoFile, setVideoFile]       = useState(null);
  const [videoResult, setVideoResult]   = useState(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoError, setVideoError]     = useState(null);
  const [videoStep, setVideoStep]       = useState(0);

  const [audioFile, setAudioFile]       = useState(null);
  const [audioResult, setAudioResult]   = useState(null);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioError, setAudioError]     = useState(null);
  const [audioStep, setAudioStep]       = useState(0);

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
      await new Promise(r => setTimeout(r, 600));
      setImageStep(2);
      const data = await analyzeImage(file);
      setImageResult(data); setImageStep(3);
      showToast('Analysis complete!');
    } catch (err) {
      const msg = getErrorMessage(err);
      setImageError(msg); showToast(msg, 'error');
    } finally { setImageLoading(false); }
  };

  const handleVideo = async (e) => {
    const file = e.target?.files?.[0] || e.dataTransfer?.files?.[0];
    if (!file) return;

    // ── Frontend format pre-validation ───────────────────────────────
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
      await new Promise(r => setTimeout(r, 600));
      setVideoStep(2);
      console.log('[handleVideo] Starting upload:', file.name);
      const data = await analyzeVideo(file);
      console.log('[handleVideo] Result:', data);
      setVideoResult(data); setVideoStep(3);
      showToast('Video analysis complete!');
    } catch (err) {
      const msg = getErrorMessage(err);
      console.error('[handleVideo] Error:', msg, err);
      setVideoError(msg);
      showToast(msg, 'error');
    } finally { setVideoLoading(false); }
  };

  const handleAudio = async (e) => {
    const file = e.target?.files?.[0] || e.dataTransfer?.files?.[0];
    if (!file) return;
    setAudioFile(file); setAudioResult(null); setAudioError(null);
    setAudioLoading(true); setAudioStep(1);
    try {
      await new Promise(r => setTimeout(r, 600));
      setAudioStep(2);
      const data = await analyzeAudio(file);
      setAudioResult(data); setAudioStep(3);
      showToast('Audio analysis complete!');
    } catch (err) {
      const msg = getErrorMessage(err);
      setAudioError(msg); showToast(msg, 'error');
    } finally { setAudioLoading(false); }
  };

  const resetImage = () => { setImageFile(null); setImagePreview(null); setImageResult(null); setImageError(null); setImageStep(0); };
  const resetVideo = () => { setVideoFile(null); setVideoResult(null); setVideoError(null); setVideoStep(0); };
  const resetAudio = () => { setAudioFile(null); setAudioResult(null); setAudioError(null); setAudioStep(0); };

  const isLoading = imageLoading || videoLoading || audioLoading;
  const curStep = activeTab === 'image' ? imageStep : activeTab === 'video' ? videoStep : audioStep;

  return (
    <div className="min-h-screen bg-[#030912] pt-16">

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`fixed top-20 right-4 z-50 px-5 py-3 rounded-xl text-sm font-medium shadow-xl ${
              toast.type === 'error'
                ? 'bg-red-900/90 border border-red-500/40 text-red-200'
                : 'bg-green-900/90 border border-green-500/40 text-green-200'
            }`}
          >
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="max-w-4xl mx-auto px-4 py-12">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10 text-center">
          <h1 className="text-4xl md:text-5xl font-bold font-['Space_Grotesk'] text-white mb-3">
            Content Detection
          </h1>
          <p className="text-gray-400 text-lg">
            Upload an image, video, or audio file to analyze its authenticity
          </p>
          <button onClick={handleTestConnection} className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition">
            Test Backend Connection
          </button>
        </motion.div>

        {/* Tab bar */}
        <div className="flex gap-2 mb-8 bg-white/3 p-1.5 rounded-2xl border border-white/8">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-4 rounded-xl font-semibold transition-all duration-200 text-sm ${
                activeTab === tab.id
                  ? `bg-gradient-to-r ${tab.gradient} text-white shadow-lg`
                  : 'text-gray-500 hover:text-white hover:bg-white/5'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Stepper (only when loading) */}
        {isLoading && <Stepper step={curStep} />}

        {/* Main panel */}
        <div className="bg-white/2 backdrop-blur-xl border border-white/8 rounded-3xl p-8 shadow-2xl">

          {/* ═══ IMAGE TAB ═══ */}
          <div className={activeTab === 'image' ? 'block' : 'hidden'}>
            <div className="space-y-5">
              {!imageFile ? (
                <DropZone id="img-upload" accept="image/*" icon={ImageIcon}
                  gradient="from-cyan-500 to-blue-600"
                  title="Upload an Image" hint="Supports: JPG, PNG, WEBP, GIF (Max 10 MB)"
                  onUpload={handleImage}
                />
              ) : (
                <>
                  {imagePreview && (
                    <div className="relative rounded-2xl overflow-hidden max-h-64">
                      <img src={imagePreview} alt="preview" className="w-full object-cover" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                    </div>
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
                  className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl text-red-300 text-sm flex gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {imageError}
                </motion.div>
              )}

              {imageResult?.image_type === 'screenshot' && (
                <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-300 text-sm flex gap-2">
                  <Info className="w-4 h-4 shrink-0 mt-0.5" />
                  Screenshot detected — deepfake analysis is optimized for photos with human faces.
                </div>
              )}

              <ResultCard result={imageResult} onReset={resetImage} />
            </div>
          </div>

          {/* ═══ VIDEO TAB ═══ */}
          <div className={activeTab === 'video' ? 'block' : 'hidden'}>
            <div className="space-y-5">
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
                  className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl text-red-300 text-sm flex gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {videoError}
                </motion.div>
              )}

              <ResultCard result={videoResult} onReset={resetVideo} />
            </div>
          </div>

          {/* ═══ AUDIO TAB ═══ */}
          <div className={activeTab === 'audio' ? 'block' : 'hidden'}>
            <div className="space-y-5">
              {!audioFile ? (
                <DropZone id="aud-upload" accept="audio/*" icon={Mic}
                  gradient="from-green-500 to-emerald-600"
                  title="Upload an Audio File" hint="Supports: MP3, WAV, M4A, OGG (Max 50 MB)"
                  onUpload={handleAudio}
                />
              ) : (
                <FileCard file={audioFile} icon={Mic}
                  gradient="from-green-500 to-emerald-600" btnLabel="Analyze Audio"
                  loading={audioLoading} onRemove={resetAudio}
                  onAnalyze={() => handleAudio({ target: { files: [audioFile] } })}
                />
              )}

              {audioError && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl text-red-300 text-sm flex gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {audioError}
                </motion.div>
              )}

              <ResultCard result={audioResult} onReset={resetAudio} />
            </div>
          </div>
        </div>

        {/* Info note */}
        <p className="text-center text-gray-600 text-xs mt-6">
          Files are processed securely and not permanently stored. Analysis uses multi-layer AI forensics.
        </p>
      </div>
    </div>
  );
};

export default Detect;
