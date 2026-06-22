import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend, BarChart, Bar
} from 'recharts';
import { getDashboardStats, getDailyStats, getRecentActivity, getTopDetections } from '../services/api';
import { Image as ImageIcon, Video, Mic, Shield, Brain, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';

const StatCard = ({ icon: Icon, label, value, color, bg, border }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`${bg} ${border} border rounded-2xl p-5 flex items-center gap-4`}
  >
    <div className={`w-12 h-12 rounded-xl ${bg} border ${border} flex items-center justify-center`}>
      <Icon className={`w-6 h-6 ${color}`} />
    </div>
    <div>
      <p className="text-gray-400 text-sm">{label}</p>
      <p className={`text-3xl font-bold font-['Space_Grotesk'] ${color}`}>{value ?? '—'}</p>
    </div>
  </motion.div>
);

const TOOLTIP_STYLE = {
  background: '#0a1628', border: '1px solid rgba(6,182,212,0.2)',
  borderRadius: '10px', color: '#fff', fontSize: '12px'
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
    } catch {
      setError('Failed to load dashboard. Is the backend running?');
    } finally { setLoading(false); }
  };

  const PIE_DATA = stats ? [
    { name: 'Image', value: stats.image_analyses || 0 },
    { name: 'Video', value: stats.video_analyses  || 0 },
    { name: 'Audio', value: stats.audio_analyses  || 0 },
  ] : [];
  const PIE_COLORS = ['#22d3ee', '#a855f7', '#22c55e'];

  const verdictColor = (v) => {
    if (!v) return 'text-gray-400';
    const l = v.toLowerCase();
    if (l.includes('authentic') && !l.includes('likely')) return 'text-green-400';
    if (l.includes('likely authentic')) return 'text-emerald-400';
    if (l.includes('ai') || l.includes('deepfake') || l.includes('manipulated')) return 'text-red-400';
    if (l.includes('suspicious')) return 'text-amber-400';
    return 'text-gray-400';
  };

  if (loading) return (
    <div className="min-h-screen bg-[#030912] flex items-center justify-center pt-16">
      <div className="text-center">
        <div className="w-12 h-12 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-400">Loading analytics…</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#030912] pt-24 px-4 pb-12">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white font-['Space_Grotesk']">Analytics Dashboard</h1>
            <p className="text-gray-500 text-sm mt-1">
              Last updated: {stats?.last_updated || new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
            </p>
          </div>
          <button onClick={fetchAll}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 text-gray-300 rounded-xl text-sm hover:bg-white/10 transition">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl text-red-300 text-sm mb-6 flex gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
          </div>
        )}

        {/* Stat Cards — row 1: content type */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <StatCard icon={ImageIcon} label="Images Analyzed" value={stats?.image_analyses}
            color="text-cyan-400" bg="bg-cyan-500/5" border="border-cyan-500/20" />
          <StatCard icon={Video} label="Videos Analyzed" value={stats?.video_analyses}
            color="text-purple-400" bg="bg-purple-500/5" border="border-purple-500/20" />
          <StatCard icon={Mic} label="Audio Analyzed" value={stats?.audio_analyses}
            color="text-green-400" bg="bg-green-500/5" border="border-green-500/20" />
        </div>

        {/* Stat Cards — row 2: verdicts */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <StatCard icon={CheckCircle} label="Authentic" value={stats?.authentic_count}
            color="text-emerald-400" bg="bg-emerald-500/5" border="border-emerald-500/20" />
          <StatCard icon={Brain} label="AI Generated" value={stats?.ai_generated_count}
            color="text-orange-400" bg="bg-orange-500/5" border="border-orange-500/20" />
          <StatCard icon={AlertTriangle} label="Deepfakes" value={stats?.deepfakes_detected}
            color="text-red-400" bg="bg-red-500/5" border="border-red-500/20" />
          <StatCard icon={Shield} label="Suspicious" value={stats?.suspicious_count}
            color="text-amber-400" bg="bg-amber-500/5" border="border-amber-500/20" />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">

          {/* Line chart */}
          <div className="lg:col-span-2 bg-white/3 border border-white/8 rounded-2xl p-6">
            <h2 className="text-white font-semibold mb-1 font-['Space_Grotesk']">Daily Detections — 30 Days</h2>
            <p className="text-gray-500 text-xs mb-5">Image · Video · Audio analyses per day</p>
            {daily.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={daily}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="date" tick={{ fill: '#4b5563', fontSize: 10 }} interval={6} />
                  <YAxis tick={{ fill: '#4b5563', fontSize: 10 }} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Line type="monotone" dataKey="image" stroke="#22d3ee" strokeWidth={2} dot={false} name="Image" />
                  <Line type="monotone" dataKey="video" stroke="#a855f7" strokeWidth={2} dot={false} name="Video" />
                  <Line type="monotone" dataKey="audio" stroke="#22c55e" strokeWidth={2} dot={false} name="Audio" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center">
                <p className="text-gray-600 text-sm">No data yet. Start analyzing content!</p>
              </div>
            )}
          </div>

          {/* Pie chart */}
          <div className="bg-white/3 border border-white/8 rounded-2xl p-6">
            <h2 className="text-white font-semibold mb-1 font-['Space_Grotesk']">By Content Type</h2>
            <p className="text-gray-500 text-xs mb-5">Distribution of all analyses</p>
            {PIE_DATA.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={4} dataKey="value">
                    {PIE_DATA.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Legend formatter={v => <span style={{ color: '#9ca3af', fontSize: '12px' }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center">
                <p className="text-gray-600 text-sm text-center">No data yet</p>
              </div>
            )}
          </div>
        </div>

        {/* Flagged Detections */}
        <div className="bg-white/3 border border-white/8 rounded-2xl p-6 mb-6">
          <h2 className="text-white font-semibold mb-4 font-['Space_Grotesk']">
            🔴 Recent High-Confidence Detections
          </h2>
          {flagged.length > 0 ? (
            <div className="space-y-3">
              {flagged.map((t, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-white/3 rounded-xl border border-white/5">
                  <div className="flex items-center gap-3">
                    <span className="text-red-400 font-bold text-sm w-6">#{i + 1}</span>
                    <p className="text-gray-300 text-sm">{t.title}</p>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <p className="text-red-400 text-sm font-bold">{t.confidence}%</p>
                    <p className="text-gray-600 text-xs">{t.date}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 text-sm text-center py-8">No suspicious content detected yet.</p>
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-white/3 border border-white/8 rounded-2xl p-6">
          <h2 className="text-white font-semibold mb-4 font-['Space_Grotesk']">🕐 Recent Activity</h2>
          {recent.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 border-b border-white/5">
                    <th className="text-left pb-3 font-medium">Type</th>
                    <th className="text-left pb-3 font-medium">Summary</th>
                    <th className="text-left pb-3 font-medium">Verdict</th>
                    <th className="text-left pb-3 font-medium">Confidence</th>
                    <th className="text-left pb-3 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/4">
                  {recent.map((row, i) => (
                    <tr key={i} className="hover:bg-white/3 transition">
                      <td className="py-3 font-medium">
                        <span className="flex items-center gap-1.5">
                          <span>{row.icon || '📄'}</span>
                          <span className="text-cyan-400">{row.type}</span>
                        </span>
                      </td>
                      <td className="py-3 text-gray-400 max-w-[180px] truncate">{row.summary}</td>
                      <td className={`py-3 font-semibold ${verdictColor(row.result)}`}>{row.result}</td>
                      <td className="py-3 text-gray-300">{row.confidence}</td>
                      <td className="py-3 text-gray-600 text-xs">{row.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-600 text-sm text-center py-8">
              No activity yet. Analyses will appear here automatically.
            </p>
          )}
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
