import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend, BarChart, Bar
} from 'recharts';
import { getDashboardStats, getDailyStats, getRecentActivity, getTopDetections } from '../services/api';
import { Image as ImageIcon, Video, Shield, Brain, AlertTriangle, CheckCircle, RefreshCw, TrendingUp } from 'lucide-react';

const StatCard = ({ icon: Icon, label, value, color, bg, border, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    whileHover={{ scale: 1.02, y: -2 }}
    className="glass-card p-5 flex items-center gap-4 cursor-default"
  >
    <motion.div
      whileHover={{ scale: 1.1, rotate: 5 }}
      className={`w-14 h-14 rounded-xl bg-gradient-to-br ${bg} border ${border} flex items-center justify-center ring-glow`}
    >
      <Icon className={`w-7 h-7 ${color}`} />
    </motion.div>
    <div>
      <p className="text-muted-foreground text-sm">{label}</p>
      <p className={`text-3xl font-bold font-display ${color}`}>{value ?? '—'}</p>
    </div>
  </motion.div>
);

const TOOLTIP_STYLE = {
  background: 'rgba(11, 15, 30, 0.95)', border: '1px solid rgba(79, 107, 255, 0.2)',
  borderRadius: '12px', color: '#fff', fontSize: '12px', backdropFilter: 'blur(20px)'
};

const Dashboard = () => {
  const [stats, setStats]   = useState(null);
  const [daily, setDaily]   = useState([]);
  const [recent, setRecent] = useState([]);
  const [flagged, setFlagged] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    setLoading(true); setError(null);
    try {
      const [s, d, r, t] = await Promise.all([
        getDashboardStats(), getDailyStats(), getRecentActivity(), getTopDetections()
      ]);
      setStats(s.data);
      setDaily(d.data.daily || []);
      setRecent(r.data.recent || []);
      setFlagged(t.data.topics || []);
    } catch (err) {
      console.error('Dashboard API error:', err);
      if (err.message === 'UNAUTHORIZED') {
        window.location.href = '/login';
        return;
      }
      if (err.response) {
        console.error('Response status:', err.response.status);
        console.error('Response data:', err.response.data);
      }
      setError(`Failed to load dashboard: ${err.message || 'Unknown error'}`);
    } finally { setLoading(false); }
  };

  const PIE_DATA = stats ? [
    { name: 'Image', value: stats.image_analyses || 0 },
    { name: 'Video', value: stats.video_analyses  || 0 },
  ] : [];
  const PIE_COLORS = ['#4F6BFF', '#9A4DFF'];

  const verdictColor = (v) => {
    if (!v) return 'text-muted-foreground';
    const l = v.toLowerCase();
    if (l.includes('authentic') && !l.includes('likely')) return 'text-green-400';
    if (l.includes('likely authentic')) return 'text-emerald-400';
    if (l.includes('ai') || l.includes('deepfake') || l.includes('manipulated')) return 'text-red-400';
    if (l.includes('suspicious')) return 'text-amber-400';
    return 'text-muted-foreground';
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center pt-16" style={{ background: 'var(--background)' }}>
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-16 h-16 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full mx-auto mb-4 ring-glow"
        />
        <p className="text-muted-foreground">Loading analytics…</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen pt-24 px-4 pb-12" style={{ background: 'var(--background)' }}>
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h1 className="text-3xl md:text-4xl font-bold font-display text-white">Analytics Dashboard</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Last updated: {stats?.last_updated || new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
            </p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={fetchAll}
            className="flex items-center gap-2 px-4 py-2 glass-strong text-muted-foreground rounded-xl text-sm hover:bg-white/5 transition-all"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </motion.button>
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 glass border-red-500/30 rounded-xl text-red-300 text-sm mb-6 flex gap-2"
          >
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
          </motion.div>
        )}

        {/* Stat Cards — row 1: content type */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <StatCard icon={ImageIcon} label="Images Analyzed" value={stats?.image_analyses}
            color="text-cyan-400" bg="from-cyan-500/20 to-blue-600/20" border="border-cyan-500/30" delay={0.1} />
          <StatCard icon={Video} label="Videos Analyzed" value={stats?.video_analyses}
            color="text-purple-400" bg="from-purple-500/20 to-pink-600/20" border="border-purple-500/30" delay={0.2} />
        </div>

        {/* Stat Cards — row 2: verdicts */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <StatCard icon={CheckCircle} label="Authentic" value={stats?.authentic_count}
            color="text-emerald-400" bg="from-emerald-500/20 to-green-600/20" border="border-emerald-500/30" delay={0.4} />
          <StatCard icon={Brain} label="AI Generated" value={stats?.ai_generated_count}
            color="text-orange-400" bg="from-orange-500/20 to-red-600/20" border="border-orange-500/30" delay={0.5} />
          <StatCard icon={AlertTriangle} label="Deepfakes" value={stats?.deepfakes_detected}
            color="text-red-400" bg="from-red-500/20 to-rose-600/20" border="border-red-500/30" delay={0.6} />
          <StatCard icon={Shield} label="Suspicious" value={stats?.suspicious_count}
            color="text-amber-400" bg="from-amber-500/20 to-yellow-600/20" border="border-amber-500/30" delay={0.7} />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">

          {/* Line chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="lg:col-span-2 glass-card-xl p-6"
          >
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              <h2 className="text-white font-semibold font-display">Daily Detections — 30 Days</h2>
            </div>
            <p className="text-muted-foreground text-xs mb-5">Image · Video analyses per day</p>
            {daily.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={daily}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="date" tick={{ fill: '#64748B', fontSize: 10 }} interval={6} />
                  <YAxis tick={{ fill: '#64748B', fontSize: 10 }} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Line type="monotone" dataKey="image" stroke="#4F6BFF" strokeWidth={2} dot={false} name="Image" />
                  <Line type="monotone" dataKey="video" stroke="#9A4DFF" strokeWidth={2} dot={false} name="Video" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center">
                <p className="text-muted-foreground text-sm">No data yet. Start analyzing content!</p>
              </div>
            )}
          </motion.div>

          {/* Pie chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="glass-card-xl p-6"
          >
            <h2 className="text-white font-semibold mb-1 font-display">By Content Type</h2>
            <p className="text-muted-foreground text-xs mb-5">Distribution of all analyses</p>
            {PIE_DATA.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={4} dataKey="value">
                    {PIE_DATA.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Legend formatter={v => <span style={{ color: '#A6ADC2', fontSize: '12px' }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center">
                <p className="text-muted-foreground text-sm text-center">No data yet</p>
              </div>
            )}
          </motion.div>
        </div>

        {/* Flagged Detections */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="glass-card-xl p-6 mb-6"
        >
          <h2 className="text-white font-semibold mb-4 font-display flex items-center gap-2">
            <span className="text-red-400">🔴</span> Recent High-Confidence Detections
          </h2>
          {flagged.length > 0 ? (
            <div className="space-y-3">
              {flagged.map((t, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 1.1 + i * 0.05 }}
                  whileHover={{ scale: 1.01, x: 4 }}
                  className="flex items-center justify-between p-3 glass rounded-xl border border-white/5 cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-red-400 font-bold text-sm w-6">#{i + 1}</span>
                    <p className="text-white text-sm">{t.title}</p>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <p className="text-red-400 text-sm font-bold">{t.confidence}%</p>
                    <p className="text-muted-foreground text-xs">{t.date}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm text-center py-8">No suspicious content detected yet.</p>
          )}
        </motion.div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
          className="glass-card-xl p-6"
        >
          <h2 className="text-white font-semibold mb-4 font-display flex items-center gap-2">
            <span>🕐</span> Recent Activity
          </h2>
          {recent.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-muted-foreground border-b border-white/10">
                    <th className="text-left pb-3 font-medium">Type</th>
                    <th className="text-left pb-3 font-medium">Summary</th>
                    <th className="text-left pb-3 font-medium">Verdict</th>
                    <th className="text-left pb-3 font-medium">Confidence</th>
                    <th className="text-left pb-3 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {recent.map((row, i) => (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1.3 + i * 0.03 }}
                      className="hover:bg-white/5 transition cursor-pointer"
                    >
                      <td className="py-3 font-medium">
                        <span className="flex items-center gap-1.5">
                          <span>{row.icon || '📄'}</span>
                          <span className="text-cyan-400">{row.type}</span>
                        </span>
                      </td>
                      <td className="py-3 text-muted-foreground max-w-[180px] truncate">{row.summary}</td>
                      <td className={`py-3 font-semibold ${verdictColor(row.result)}`}>{row.result}</td>
                      <td className="py-3 text-white">{row.confidence}</td>
                      <td className="py-3 text-muted-foreground text-xs">{row.date}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted-foreground text-sm text-center py-8">
              No activity yet. Analyses will appear here automatically.
            </p>
          )}
        </motion.div>

      </div>
    </div>
  );
};

export default Dashboard;
