import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getUserHistory, deleteHistoryItem } from '../services/api';
import { Image as ImageIcon, Video, Search, Filter, Trash2, AlertTriangle, Clock, ChevronDown, X } from 'lucide-react';

const TYPE_ICONS = { Image: ImageIcon, Video: Video };
const TYPE_COLORS = {
  Image: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
  Video: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
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
      const data = res.data;
      if (Array.isArray(data)) {
        setItems(data);
      } else if (data && Array.isArray(data.items)) {
        setItems(data.items);
      } else {
        setItems([]);
      }
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
    <div className="min-h-screen flex items-center justify-center pt-16" style={{ background: 'var(--background)' }}>
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-16 h-16 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full mx-auto mb-4 ring-glow"
        />
        <p className="text-muted-foreground">Loading history…</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen pt-24 px-4 pb-12" style={{ background: 'var(--background)' }}>
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold font-display text-white mb-1">Detection History</h1>
          <p className="text-muted-foreground text-sm">All your previous content authenticity analyses</p>
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

        {/* Search + Filter bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6 space-y-3"
        >
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search by type or verdict…"
                className="w-full pl-10 pr-4 py-2.5 glass-strong rounded-xl text-white placeholder:text-muted-foreground/60 text-sm focus:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand/20 transition-all"
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowFilters(p => !p)}
              className={`flex items-center gap-2 px-4 py-2.5 glass-strong rounded-xl text-muted-foreground text-sm hover:bg-white/5 transition-all ${showFilters ? 'bg-brand/10 text-brand border-brand/30' : ''}`}
            >
              <Filter className="w-4 h-4" /> Filters
              <ChevronDown className={`w-3 h-3 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
            </motion.button>
          </div>

          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="glass-card p-4 space-y-4">
                  <div>
                    <p className="text-muted-foreground text-xs mb-2 uppercase tracking-wider">Type</p>
                    <div className="flex gap-2">
                      {['All', 'Image', 'Video'].map(t => (
                        <motion.button
                          key={t}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => setTypeFilter(t)}
                          className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${typeFilter === t ? 'bg-brand text-white ring-glow' : 'glass text-muted-foreground hover:text-white'}`}
                        >
                          {t}
                        </motion.button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs mb-2 uppercase tracking-wider">Verdict</p>
                    <div className="flex flex-wrap gap-2">
                      {['All', 'Authentic', 'Suspicious', 'AI Generated', 'Deepfake', 'Manipulated'].map(v => (
                        <motion.button
                          key={v}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => setVFilter(v)}
                          className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${verdictFilter === v ? 'bg-brand text-white ring-glow' : 'glass text-muted-foreground hover:text-white'}`}
                        >
                          {v}
                        </motion.button>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Summary */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex items-center gap-3 mb-4"
        >
          <span className="text-muted-foreground text-sm">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
          {(search || typeFilter !== 'All' || verdictFilter !== 'All') && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => { setSearch(''); setTypeFilter('All'); setVFilter('All'); }}
              className="flex items-center gap-1 text-cyan-400 text-xs hover:underline"
            >
              <X className="w-3 h-3" /> Clear filters
            </motion.button>
          )}
        </motion.div>

        {/* History list */}
        {filtered.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-20 glass-card-xl"
          >
            <Clock className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
            <p className="text-muted-foreground">
              {items.length === 0 ? 'No analyses yet. Start detecting content!' : 'No results match your filters.'}
            </p>
          </motion.div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {filtered.map((item, i) => {
                const Icon = TYPE_ICONS[item.type] || ImageIcon;
                const typeStyle = TYPE_COLORS[item.type] || 'text-muted-foreground glass border-white/10';
                const vColor = Object.entries(VERDICT_COLORS).find(([k]) => (item.result || '').includes(k))?.[1] || 'text-muted-foreground';
                return (
                  <motion.div
                    key={item.analysis_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20, height: 0 }}
                    transition={{ delay: i * 0.05 }}
                    whileHover={{ scale: 1.01, x: 4 }}
                    className="flex items-center gap-4 p-4 glass-card cursor-pointer group"
                  >
                    {/* Type icon */}
                    <motion.div
                      whileHover={{ scale: 1.1, rotate: 5 }}
                      className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border ${typeStyle} ring-glow`}
                    >
                      <Icon className="w-6 h-6" />
                    </motion.div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${typeStyle}`}>
                          {item.type}
                        </span>
                        <span className={`text-sm font-semibold ${vColor}`}>{item.result || 'Unknown'}</span>
                      </div>
                      <p className="text-muted-foreground text-xs">{fmtDate(item.created_at)}</p>
                    </div>

                    {/* Confidence */}
                    <div className="text-right shrink-0">
                      <p className="text-white font-bold text-sm font-display">{fmt(item.confidence)}</p>
                      <p className="text-muted-foreground text-xs">confidence</p>
                    </div>

                    {/* Delete */}
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => handleDelete(item.analysis_id)}
                      disabled={deleting === item.analysis_id}
                      className="opacity-0 group-hover:opacity-100 p-2 glass text-muted-foreground hover:text-red-400 hover:bg-red-500/10 rounded-lg transition disabled:opacity-50"
                    >
                      {deleting === item.analysis_id
                        ? <div className="w-4 h-4 border border-red-400/50 border-t-red-400 rounded-full animate-spin" />
                        : <Trash2 className="w-4 h-4" />
                      }
                    </motion.button>
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
