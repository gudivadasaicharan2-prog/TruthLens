import { motion, useScroll, useTransform } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useRef, useState, useEffect } from 'react';
import {
  Shield, Image as ImageIcon, Video, Mic, ArrowRight,
  CheckCircle, Zap, Lock, Eye, Brain, Upload, ChevronDown,
  Star, Activity, Globe, Clock
} from 'lucide-react';

/* ── Animated floating particle ── */
const Particle = ({ x, y, size, delay, color }) => (
  <motion.div
    className="absolute rounded-full opacity-20 blur-sm pointer-events-none"
    style={{ left: `${x}%`, top: `${y}%`, width: size, height: size, background: color }}
    animate={{ y: [0, -30, 0], opacity: [0.1, 0.3, 0.1] }}
    transition={{ duration: 4 + delay, repeat: Infinity, delay, ease: 'easeInOut' }}
  />
);

/* ── Animated counter ── */
const Counter = ({ target, suffix = '' }) => {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !started) { setStarted(true); }
    }, { threshold: 0.5 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [started]);

  useEffect(() => {
    if (!started) return;
    let start = 0;
    const step = Math.ceil(target / 60);
    const t = setInterval(() => {
      start = Math.min(start + step, target);
      setCount(start);
      if (start >= target) clearInterval(t);
    }, 24);
    return () => clearInterval(t);
  }, [started, target]);

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>;
};

const Landing = () => {
  const navigate = useNavigate();
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: heroRef });
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const heroY = useTransform(scrollYProgress, [0, 0.5], [0, -60]);

  const particles = [
    { x: 10, y: 20, size: 60, delay: 0, color: '#22d3ee' },
    { x: 80, y: 10, size: 40, delay: 1, color: '#3b82f6' },
    { x: 60, y: 60, size: 80, delay: 2, color: '#8b5cf6' },
    { x: 20, y: 70, size: 50, delay: 0.5, color: '#22d3ee' },
    { x: 90, y: 80, size: 35, delay: 1.5, color: '#3b82f6' },
    { x: 40, y: 30, size: 25, delay: 3, color: '#8b5cf6' },
    { x: 70, y: 90, size: 45, delay: 0.8, color: '#22d3ee' },
  ];

  const features = [
    {
      icon: ImageIcon,
      title: 'Image Analysis',
      desc: 'Detect AI-generated images, deepfakes, and manipulation with pixel-level forensic analysis, EXIF inspection, and manipulation heatmaps.',
      color: 'cyan',
      gradient: 'from-cyan-500 to-blue-600',
      badge: 'EXIF · Forensics · Heatmap',
      link: '/detect',
    },
    {
      icon: Video,
      title: 'Video Detection',
      desc: 'Frame-by-frame deepfake detection with face consistency scoring, lip-sync analysis, and timeline of suspicious segments.',
      color: 'purple',
      gradient: 'from-purple-500 to-pink-600',
      badge: 'Face Swap · Lip Sync · Frames',
      link: '/detect',
    },
    {
      icon: Mic,
      title: 'Audio Verification',
      desc: 'Identify voice clones and AI-synthesized speech using spectrogram analysis, pitch variance detection, and acoustic fingerprinting.',
      color: 'green',
      gradient: 'from-green-500 to-emerald-600',
      badge: 'Voice Clone · Spectrogram · Waveform',
      link: '/detect',
    },
  ];

  const verdicts = [
    { label: 'Authentic', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30', icon: '✅' },
    { label: 'Likely Authentic', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', icon: '✅' },
    { label: 'Suspicious', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', icon: '⚠️' },
    { label: 'AI Generated', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30', icon: '🤖' },
    { label: 'Deepfake', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', icon: '❌' },
    { label: 'Manipulated', color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30', icon: '✂️' },
  ];

  const stats = [
    { icon: Activity, value: 94, suffix: '.7%', label: 'Detection Accuracy', color: 'text-cyan-400' },
    { icon: Clock, value: 1, suffix: 's', label: 'Avg. Analysis Time', color: 'text-green-400' },
    { icon: Globe, value: 50, suffix: 'K+', label: 'Files Analyzed', color: 'text-purple-400' },
    { icon: Star, value: 99, suffix: '%', label: 'User Satisfaction', color: 'text-yellow-400' },
  ];

  const steps = [
    {
      step: '01', icon: Upload, title: 'Upload Your File',
      desc: 'Drag and drop or click to upload any image, video, or audio file. Supports all major formats.',
      color: 'from-cyan-500 to-blue-600',
    },
    {
      step: '02', icon: Brain, title: 'AI Analysis',
      desc: 'Our multi-layer AI forensic engine analyzes every pixel, frame, and audio sample for signs of manipulation.',
      color: 'from-blue-500 to-purple-600',
    },
    {
      step: '03', icon: Eye, title: 'View Results',
      desc: 'Get a clear verdict with confidence score, key findings, and optional advanced forensic breakdown.',
      color: 'from-purple-500 to-pink-600',
    },
  ];

  return (
    <div className="min-h-screen bg-[#030912] text-white overflow-x-hidden">

      {/* ── HERO ── */}
      <section ref={heroRef} className="relative min-h-screen flex flex-col items-center justify-center px-4 pt-16 overflow-hidden">

        {/* Animated grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(6,182,212,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(6,182,212,0.03)_1px,transparent_1px)] bg-[size:64px_64px]" />

        {/* Radial glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-10%,rgba(6,182,212,0.12),transparent)]" />

        {/* Floating particles */}
        {particles.map((p, i) => <Particle key={i} {...p} />)}

        <motion.div
          style={{ opacity: heroOpacity, y: heroY }}
          className="relative z-10 text-center max-w-5xl mx-auto"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 mb-8 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full"
          >
            <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
            <span className="text-cyan-400 text-sm font-medium tracking-wide">AI-Powered Deepfake Detection Platform</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-5xl md:text-7xl lg:text-8xl font-bold font-['Space_Grotesk'] leading-[1.05] mb-6"
          >
            Detect{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500">
              AI Content
            </span>
            <br />& Deepfakes with{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500">
              Confidence
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-lg md:text-xl text-gray-400 mb-10 max-w-3xl mx-auto leading-relaxed"
          >
            Upload any image, video, or audio file and instantly determine whether it's real, AI-generated,
            manipulated, or a deepfake — powered by multi-layer forensic AI.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex flex-wrap gap-4 justify-center mb-12"
          >
            <Link
              to="/detect?tab=image"
              className="group flex items-center gap-2 px-6 py-3 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-xl font-semibold hover:bg-cyan-500/20 transition-all"
            >
              <ImageIcon className="w-5 h-5" /> Upload Image
            </Link>
            <Link
              to="/detect?tab=video"
              className="group flex items-center gap-2 px-6 py-3 bg-purple-500/10 border border-purple-500/30 text-purple-400 rounded-xl font-semibold hover:bg-purple-500/20 transition-all"
            >
              <Video className="w-5 h-5" /> Upload Video
            </Link>
            <Link
              to="/detect?tab=audio"
              className="group flex items-center gap-2 px-6 py-3 bg-green-500/10 border border-green-500/30 text-green-400 rounded-xl font-semibold hover:bg-green-500/20 transition-all"
            >
              <Mic className="w-5 h-5" /> Upload Audio
            </Link>
          </motion.div>

          {/* Main CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
          >
            <button
              onClick={() => navigate('/detect')}
              className="group px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-2xl font-bold text-lg hover:shadow-2xl hover:shadow-cyan-500/25 transition-all duration-300 flex items-center justify-center gap-2"
            >
              Start Detection Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => navigate('/register')}
              className="px-8 py-4 border border-white/10 text-gray-300 rounded-2xl font-semibold text-lg hover:bg-white/5 transition-all flex items-center justify-center gap-2"
            >
              <Shield className="w-5 h-5 text-cyan-400" /> Create Free Account
            </button>
          </motion.div>

          {/* Trust badges */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="flex flex-wrap justify-center gap-6 text-sm text-gray-500"
          >
            {[
              { icon: CheckCircle, text: 'No signup required to detect', color: 'text-green-500' },
              { icon: Lock, text: 'Files not stored', color: 'text-cyan-500' },
              { icon: Zap, text: 'Results in under 10 seconds', color: 'text-yellow-500' },
            ].map(({ icon: Icon, text, color }) => (
              <div key={text} className="flex items-center gap-2">
                <Icon className={`w-4 h-4 ${color}`} />
                <span>{text}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
        >
          <ChevronDown className="w-6 h-6 text-gray-600" />
        </motion.div>
      </section>

      {/* ── VERDICT SHOWCASE ── */}
      <section className="py-16 px-4 bg-gradient-to-b from-[#030912] to-[#070f1e]">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-10"
          >
            <p className="text-gray-500 text-sm uppercase tracking-widest mb-3">Possible Verdicts</p>
            <h2 className="text-2xl font-bold text-white">Every result is clear and actionable</h2>
          </motion.div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {verdicts.map((v, i) => (
              <motion.div
                key={v.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07 }}
                className={`${v.bg} ${v.border} border rounded-xl p-4 text-center`}
              >
                <div className="text-2xl mb-2">{v.icon}</div>
                <p className={`text-sm font-semibold ${v.color}`}>{v.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="py-24 px-4">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-block mb-4 px-4 py-1.5 bg-cyan-500/10 border border-cyan-500/20 rounded-full">
              <span className="text-cyan-400 text-sm font-medium">Detection Capabilities</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold font-['Space_Grotesk'] text-white mb-4">
              Three content types.<br />One powerful platform.
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto text-lg">
              Enterprise-grade AI forensics for images, videos, and audio — all in one place.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="group relative bg-white/3 hover:bg-white/5 border border-white/8 hover:border-white/15 rounded-3xl p-8 transition-all duration-300 cursor-pointer overflow-hidden"
                onClick={() => navigate(f.link)}
              >
                {/* Glow on hover */}
                <div className={`absolute inset-0 bg-gradient-to-br ${f.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300 rounded-3xl`} />

                <div className={`w-14 h-14 bg-gradient-to-br ${f.gradient} rounded-2xl flex items-center justify-center mb-6 shadow-lg`}>
                  <f.icon className="w-7 h-7 text-white" />
                </div>

                <h3 className="text-xl font-bold text-white mb-3 font-['Space_Grotesk']">{f.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed mb-6">{f.desc}</p>

                <div className={`inline-flex items-center gap-1.5 px-3 py-1 bg-${f.color}-500/10 border border-${f.color}-500/20 rounded-full`}>
                  <span className={`text-${f.color}-400 text-xs font-medium`}>{f.badge}</span>
                </div>

                <div className="mt-6 flex items-center gap-2 text-gray-500 group-hover:text-white transition-colors">
                  <span className="text-sm">Try it now</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="py-24 px-4 bg-gradient-to-b from-transparent to-[#070f1e]">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-block mb-4 px-4 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full">
              <span className="text-blue-400 text-sm font-medium">How It Works</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold font-['Space_Grotesk'] text-white mb-4">
              Results in 3 simple steps
            </h2>
          </motion.div>

          <div className="relative">
            {/* Connecting line */}
            <div className="hidden md:block absolute top-14 left-1/4 right-1/4 h-px bg-gradient-to-r from-cyan-500/50 via-blue-500/50 to-purple-500/50" />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {steps.map((s, i) => (
                <motion.div
                  key={s.step}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.2 }}
                  className="relative text-center"
                >
                  <div className={`w-28 h-28 mx-auto mb-6 rounded-3xl bg-gradient-to-br ${s.color} p-0.5`}>
                    <div className="w-full h-full bg-[#070f1e] rounded-3xl flex flex-col items-center justify-center gap-2">
                      <s.icon className="w-8 h-8 text-white" />
                      <span className="text-xs font-bold text-gray-500">{s.step}</span>
                    </div>
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2 font-['Space_Grotesk']">{s.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{s.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── STATISTICS ── */}
      <section className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-block mb-4 px-4 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-full">
              <span className="text-purple-400 text-sm font-medium">Platform Statistics</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold font-['Space_Grotesk'] text-white">
              Trusted results, proven accuracy
            </h2>
          </motion.div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-white/3 border border-white/8 rounded-2xl p-6 text-center"
              >
                <s.icon className={`w-6 h-6 ${s.color} mx-auto mb-3`} />
                <div className={`text-3xl md:text-4xl font-bold font-['Space_Grotesk'] ${s.color} mb-1`}>
                  <Counter target={s.value} suffix={s.suffix} />
                </div>
                <p className="text-gray-500 text-sm">{s.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-24 px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-blue-500/5 to-purple-500/5" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_60%_at_50%_50%,rgba(6,182,212,0.08),transparent)]" />

        <div className="max-w-3xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-6xl font-bold font-['Space_Grotesk'] text-white mb-6">
              Start detecting{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">
                right now
              </span>
            </h2>
            <p className="text-gray-400 text-lg mb-10">
              No signup required. Upload a file and get your authenticity verdict in seconds.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => navigate('/detect')}
                className="group px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-2xl font-bold text-lg hover:shadow-2xl hover:shadow-cyan-500/25 transition-all duration-300 flex items-center justify-center gap-2"
              >
                Analyze Content Now
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                onClick={() => navigate('/register')}
                className="px-8 py-4 border border-white/10 text-gray-300 rounded-2xl font-semibold text-lg hover:bg-white/5 transition-all"
              >
                Create Free Account
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="py-12 px-4 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <span className="text-white font-bold text-xl font-['Space_Grotesk']">TruthLens</span>
              <span className="ml-2 text-gray-600 text-sm">AI Content Authenticity Platform</span>
            </div>
            <p className="text-gray-600 text-sm">© 2026 TruthLens. All rights reserved.</p>
            <div className="flex gap-6">
              {['Privacy', 'Terms', 'Contact'].map(link => (
                <a key={link} href="#" className="text-gray-600 hover:text-cyan-400 transition-colors text-sm">{link}</a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
