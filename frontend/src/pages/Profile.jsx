import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  User, Mail, Shield, Calendar, Settings, Bell, Lock,
  Activity, Clock, ArrowRight, Edit, CheckCircle2,
  AlertTriangle, Image as ImageIcon, Video, Mic, Brain, Globe
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getUserHistory, getUserProfile } from '../services/api';
import { useNavigate } from 'react-router-dom';

const TYPE_ICONS = { image: ImageIcon, video: Video, audio: Mic };
const TYPE_COLORS = {
  image: { text: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
  video: { text: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
  audio: { text: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
};

const verdictColor = (v = '') => {
  const l = v.toLowerCase();
  if (l.includes('authentic') && !l.includes('likely')) return 'text-green-400 bg-green-500/10 border-green-500/20';
  if (l.includes('likely authentic')) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  if (l.includes('ai') || l.includes('deepfake') || l.includes('manipulated')) return 'text-red-400 bg-red-500/10 border-red-500/20';
  if (l.includes('suspicious')) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
  return 'text-gray-400 bg-white/5 border-white/10';
};

const Profile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    getUserHistory()
      .then(res => setHistory(Array.isArray(res.data) ? res.data : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="min-h-screen bg-[#030912] flex items-center justify-center pt-16">
      <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
    </div>
  );

  /* ── Derived stats ── */
  const totalAnalyses = history.length;
  const authentic = history.filter(h => (h.result || '').toLowerCase().includes('authentic')).length;
  const flagged   = history.filter(h => {
    const l = (h.result || '').toLowerCase();
    return l.includes('ai') || l.includes('deepfake') || l.includes('manipulated') || l.includes('suspicious');
  }).length;
  const byType = {
    Image: history.filter(h => (h.type || '').toLowerCase() === 'image').length,
    Video: history.filter(h => (h.type || '').toLowerCase() === 'video').length,
    Audio: history.filter(h => (h.type || '').toLowerCase() === 'audio').length,
  };

  const overviewStats = [
    { label: 'Total Analyses', value: totalAnalyses, icon: Activity, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    { label: 'Authentic Content', value: authentic, icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/10' },
    { label: 'Flagged Content', value: flagged, icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10' },
  ];

  const TABS = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'activity', label: 'Activity', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#030912] pt-24 px-4 pb-12">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-3xl font-bold text-white font-['Space_Grotesk']">My Profile</h1>
          <p className="text-gray-500 text-sm mt-1">Manage your account and detection history</p>
        </motion.div>

        {/* Profile Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="bg-white/3 border border-white/8 rounded-3xl p-6 mb-6"
        >
          <div className="flex flex-col sm:flex-row items-start gap-6">
            {/* Avatar */}
            <div className="relative shrink-0">
              {user?.picture ? (
                <img src={user.picture} alt={user.name} className="w-20 h-20 rounded-2xl object-cover" />
              ) : (
                <div className="w-20 h-20 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-3xl">
                    {user?.name?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
              )}
              <button className="absolute -bottom-2 -right-2 w-7 h-7 bg-cyan-500 hover:bg-cyan-400 rounded-full flex items-center justify-center transition shadow">
                <Edit className="w-3.5 h-3.5 text-white" />
              </button>
            </div>

            {/* Info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <h2 className="text-2xl font-bold text-white font-['Space_Grotesk']">{user?.name || 'User'}</h2>
                <span className="px-2.5 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-cyan-400 text-xs font-medium capitalize">
                  {user?.role || 'user'}
                </span>
                {user?.provider === 'google' && (
                  <span className="px-2.5 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-xs font-medium">
                    Google
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-gray-400">
                <div className="flex items-center gap-2"><Mail className="w-4 h-4 text-cyan-400" />{user?.email}</div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-cyan-400" />
                  {user?.created_at
                    ? `Member since ${new Date(user.created_at).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}`
                    : 'Member since 2026'}
                </div>
                <div className="flex items-center gap-2"><Shield className="w-4 h-4 text-cyan-400" />Account verified</div>
                <div className="flex items-center gap-2"><Globe className="w-4 h-4 text-cyan-400" />UTC+05:30</div>
              </div>
            </div>

            {/* Quick type breakdown */}
            <div className="flex gap-3 shrink-0">
              {Object.entries(byType).map(([type, count]) => {
                const c = TYPE_COLORS[type.toLowerCase()] || {};
                const Icon = TYPE_ICONS[type.toLowerCase()] || Activity;
                return (
                  <div key={type} className={`text-center px-3 py-2 ${c.bg} border ${c.border} rounded-xl`}>
                    <Icon className={`w-4 h-4 ${c.text} mx-auto mb-1`} />
                    <p className="text-white font-bold text-lg">{count}</p>
                    <p className={`text-xs ${c.text}`}>{type}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-white/3 p-1 rounded-xl border border-white/8">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium text-sm transition-all ${
                activeTab === tab.id
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/25'
                  : 'text-gray-500 hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" /> {tab.label}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW ── */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {overviewStats.map((s, i) => (
                <motion.div
                  key={s.label}
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-white/3 border border-white/8 rounded-2xl p-5"
                >
                  <div className={`w-10 h-10 ${s.bg} rounded-xl flex items-center justify-center mb-3`}>
                    <s.icon className={`w-5 h-5 ${s.color}`} />
                  </div>
                  <p className="text-3xl font-bold text-white font-['Space_Grotesk']">{s.value}</p>
                  <p className="text-gray-500 text-sm mt-1">{s.label}</p>
                </motion.div>
              ))}
            </div>

            {/* Recent 5 */}
            <div className="bg-white/3 border border-white/8 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2 font-['Space_Grotesk']">
                  <Clock className="w-4 h-4 text-cyan-400" /> Recent Activity
                </h3>
                <button onClick={() => navigate('/history')} className="text-cyan-400 text-xs hover:underline flex items-center gap-1">
                  View all <ArrowRight className="w-3 h-3" />
                </button>
              </div>
              {history.slice(0, 5).map((item, i) => {
                const tl = (item.type || 'image').toLowerCase();
                const Icon = TYPE_ICONS[tl] || Activity;
                const tc = TYPE_COLORS[tl] || {};
                return (
                  <div key={i} className="flex items-center gap-3 py-3 border-b border-white/5 last:border-0">
                    <div className={`w-9 h-9 ${tc.bg} border ${tc.border} rounded-xl flex items-center justify-center shrink-0`}>
                      <Icon className={`w-4 h-4 ${tc.text}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-300 text-sm font-medium">{item.type} Analysis</p>
                      <p className="text-gray-600 text-xs">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                      </p>
                    </div>
                    <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${verdictColor(item.result)}`}>
                      {item.result || 'Unknown'}
                    </span>
                    <span className="text-white text-sm font-bold shrink-0">
                      {item.confidence != null ? `${Math.round(item.confidence <= 1 ? item.confidence * 100 : item.confidence)}%` : '—'}
                    </span>
                  </div>
                );
              })}
              {history.length === 0 && (
                <p className="text-gray-600 text-sm text-center py-6">No analyses yet. Start detecting!</p>
              )}
            </div>
          </div>
        )}

        {/* ── ACTIVITY ── */}
        {activeTab === 'activity' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="bg-white/3 border border-white/8 rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4 font-['Space_Grotesk'] flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" /> Full Detection History
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 border-b border-white/5 text-left">
                    <th className="pb-3 font-medium">Type</th>
                    <th className="pb-3 font-medium">Verdict</th>
                    <th className="pb-3 font-medium">Confidence</th>
                    <th className="pb-3 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/4">
                  {history.map((item, i) => {
                    const tl = (item.type || '').toLowerCase();
                    const Icon = TYPE_ICONS[tl] || Activity;
                    const tc = TYPE_COLORS[tl] || { text: 'text-gray-400', bg: 'bg-white/5', border: 'border-white/10' };
                    const conf = item.confidence != null ? Math.round(item.confidence <= 1 ? item.confidence * 100 : item.confidence) : null;
                    return (
                      <tr key={i} className="hover:bg-white/3 transition">
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className={`w-7 h-7 ${tc.bg} border ${tc.border} rounded-lg flex items-center justify-center`}>
                              <Icon className={`w-3.5 h-3.5 ${tc.text}`} />
                            </div>
                            <span className="text-gray-300 capitalize">{item.type}</span>
                          </div>
                        </td>
                        <td className="py-3">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${verdictColor(item.result)}`}>
                            {item.result || 'Unknown'}
                          </span>
                        </td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-white/5 rounded-full overflow-hidden">
                              <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${conf || 0}%` }} />
                            </div>
                            <span className="text-gray-300 font-medium">{conf != null ? `${conf}%` : '—'}</span>
                          </div>
                        </td>
                        <td className="py-3 text-gray-500 text-xs">
                          {item.created_at ? new Date(item.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {history.length === 0 && (
                <p className="text-gray-600 text-sm text-center py-8">No analyses yet.</p>
              )}
            </div>
          </motion.div>
        )}

        {/* ── SETTINGS ── */}
        {activeTab === 'settings' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            <div className="bg-white/3 border border-white/8 rounded-2xl p-6">
              <h3 className="text-white font-semibold mb-4 font-['Space_Grotesk'] flex items-center gap-2">
                <Settings className="w-4 h-4 text-cyan-400" /> Account Settings
              </h3>
              <div className="space-y-2">
                {[
                  { icon: Edit, label: 'Edit Profile', desc: 'Update your name and email' },
                  { icon: Lock, label: 'Change Password', desc: 'Update your security credentials' },
                  { icon: Bell, label: 'Notifications', desc: 'Manage notification preferences' },
                ].map(({ icon: Icon, label, desc }) => (
                  <button key={label} className="w-full flex items-center justify-between p-4 bg-white/2 hover:bg-white/5 border border-white/5 rounded-xl transition group">
                    <div className="flex items-center gap-3">
                      <Icon className="w-4 h-4 text-cyan-400" />
                      <div className="text-left">
                        <p className="text-white text-sm font-medium">{label}</p>
                        <p className="text-gray-500 text-xs">{desc}</p>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-white/3 border border-white/8 rounded-2xl p-6">
              <h3 className="text-white font-semibold mb-4 font-['Space_Grotesk'] flex items-center gap-2">
                <Brain className="w-4 h-4 text-cyan-400" /> Detection Preferences
              </h3>
              <div className="space-y-2">
                {[
                  { label: 'Auto-save analyses to history', enabled: true },
                  { label: 'Show advanced forensic details by default', enabled: false },
                  { label: 'Email notification on high-risk detection', enabled: false },
                ].map(({ label, enabled }) => (
                  <div key={label} className="flex items-center justify-between p-4 bg-white/2 border border-white/5 rounded-xl">
                    <p className="text-gray-300 text-sm">{label}</p>
                    <div className={`w-10 h-5 rounded-full relative transition-colors ${enabled ? 'bg-cyan-500' : 'bg-white/10'}`}>
                      <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${enabled ? 'right-0.5' : 'left-0.5'}`} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Profile;
