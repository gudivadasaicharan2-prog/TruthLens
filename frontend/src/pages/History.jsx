import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getUserHistory, deleteHistoryItem } from '../services/api';
import { Image as ImageIcon, Video, Mic, Search, Filter, Trash2, AlertTriangle, Clock, ChevronDown } from 'lucide-react';

const TYPE_ICONS = { Image: ImageIcon, Video: Video, Audio: Mic };
const TYPE_COLORS = {
  Image: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  Video: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  Audio: 'text-green-400 bg-green-500/10 border-green-500/20',
};
const VERDICT_COLORS = {
  'Authentic': 'text-green-400',
  'Likely Authentic': 'text-emerald-400',
  'Suspicious': 'text-amber-400',
  'Likely AI Generated': 'text-orange-400',
  'AI Generated': 'text-red-400',
  'Deepfake': 'text-red-400',
  'Manipulated': 'text-rose-400',
};

const History = () => {
  const [items, setItems]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [search, setSearch]         = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [verdictFilter, setVFilter] = useState('All');
  const [deleting, setDeleting]     = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const res = await getUserHistory();
      setItems(Array.isArray(res.data) ? res.data : []);
    } catch {
      setError('Failed to load history. Make sure you are logged in.');
    } finally { setLoading(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this history entry?')) return;
    setDeleting(id);
    try {
      await deleteHistoryItem(id);
      setItems(prev => prev.filter(x => x.analysis_id !== id));
    } catch {
      alert('Failed to delete item.');
    } finally { setDeleting(null); }
  };

  const filtered = items.filter(item => {
    const matchType    = typeFilter === 'All' || item.type === typeFilter;
    const matchVerdict = verdictFilter === 'All' || (item.result || '').includes(verdictFilter);
    const matchSearch  = search === '' || (item.result || '').toLowerCase().includes(search.toLowerCase())
                       || (item.type || '').toLowerCase().includes(search.toLowerCase());
    return matchType && matchVerdict && matchSearch;
  });

  const fmt = (conf) => {
    if (conf === null || conf === undefined) return 'N/A';
    const n = parseFloat(conf);
    if (isNaN(n)) return 'N/A';
    return `${Math.round(n <= 1.0 ? n * 100 : n)}%`;
  };

  const fmtDate = (iso) => {
    if (!iso) return '—';
    try { return new Date(iso).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return iso; }
  };

  if (loading) return (
    <div className="min-h-screen bg-[#030912] flex items-center justify-center pt-16">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-500 text-sm">Loading history…</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#030912] pt-24 px-4 pb-12">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-3xl font-bold text-white font-['Space_Grotesk'] mb-1">Detection History</h1>
          <p className="text-gray-500 text-sm">All your previous content authenticity analyses</p>
        </motion.div>

        {error && (
          <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl text-red-300 text-sm mb-6 flex gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
          </div>
        )}

        {/* Search + Filter bar */}
        <div className="mb-6 space-y-3">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search by type or verdict…"
                className="w-full pl-10 pr-4 py-2.5 bg-white/3 border border-white/8 rounded-xl text-white placeholder-gray-600 text-sm focus:border-cyan-500/40 focus:outline-none transition"
              />
            </div>
            <button
              onClick={() => setShowFilters(p => !p)}
              className="flex items-center gap-2 px-4 py-2.5 bg-white/3 border border-white/8 rounded-xl text-gray-300 text-sm hover:bg-white/5 transition"
            >
              <Filter className="w-4 h-4" /> Filters
              <ChevronDown className={`w-3 h-3 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
            </button>
          </div>

          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="flex flex-wrap gap-3 pt-1">
                  <div>
                    <p className="text-gray-600 text-xs mb-1.5 uppercase tracking-wider">Type</p>
                    <div className="flex gap-2">
                      {['All', 'Image', 'Video', 'Audio'].map(t => (
                        <button key={t} onClick={() => setTypeFilter(t)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${typeFilter === t ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-white/3 text-gray-400 border border-white/8 hover:text-white'}`}>
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-gray-600 text-xs mb-1.5 uppercase tracking-wider">Verdict</p>
                    <div className="flex flex-wrap gap-2">
                      {['All', 'Authentic', 'Suspicious', 'AI Generated', 'Deepfake', 'Manipulated'].map(v => (
                        <button key={v} onClick={() => setVFilter(v)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${verdictFilter === v ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-white/3 text-gray-400 border border-white/8 hover:text-white'}`}>
                          {v}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Summary */}
        <div className="flex items-center gap-3 mb-4">
          <span className="text-gray-500 text-sm">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
          {(search || typeFilter !== 'All' || verdictFilter !== 'All') && (
            <button onClick={() => { setSearch(''); setTypeFilter('All'); setVFilter('All'); }}
              className="text-cyan-400 text-xs hover:underline">Clear filters</button>
          )}
        </div>

        {/* History list */}
        {filtered.length === 0 ? (
          <div className="text-center py-20">
            <Clock className="w-12 h-12 text-gray-700 mx-auto mb-4" />
            <p className="text-gray-500">
              {items.length === 0 ? 'No analyses yet. Start detecting content!' : 'No results match your filters.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {filtered.map((item, i) => {
                const Icon = TYPE_ICONS[item.type] || ImageIcon;
                const typeStyle = TYPE_COLORS[item.type] || 'text-gray-400 bg-white/5 border-white/10';
                const vColor = Object.entries(VERDICT_COLORS).find(([k]) => (item.result || '').includes(k))?.[1] || 'text-gray-400';
                return (
                  <motion.div
                    key={item.analysis_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20, height: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="flex items-center gap-4 p-4 bg-white/2 border border-white/6 rounded-2xl hover:bg-white/4 hover:border-white/10 transition group"
                  >
                    {/* Type icon */}
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${typeStyle}`}>
                      <Icon className="w-5 h-5" />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${typeStyle}`}>
                          {item.type}
                        </span>
                        <span className={`text-sm font-semibold ${vColor}`}>{item.result || 'Unknown'}</span>
                      </div>
                      <p className="text-gray-600 text-xs">{fmtDate(item.created_at)}</p>
                    </div>

                    {/* Confidence */}
                    <div className="text-right shrink-0">
                      <p className="text-white font-bold text-sm">{fmt(item.confidence)}</p>
                      <p className="text-gray-600 text-xs">confidence</p>
                    </div>

                    {/* Delete */}
                    <button
                      onClick={() => handleDelete(item.analysis_id)}
                      disabled={deleting === item.analysis_id}
                      className="opacity-0 group-hover:opacity-100 p-2 text-gray-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition disabled:opacity-50"
                    >
                      {deleting === item.analysis_id
                        ? <div className="w-4 h-4 border border-red-400/50 border-t-red-400 rounded-full animate-spin" />
                        : <Trash2 className="w-4 h-4" />
                      }
                    </button>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
};

export default History;
