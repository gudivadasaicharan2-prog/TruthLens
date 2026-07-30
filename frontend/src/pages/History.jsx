import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getUserHistory, deleteHistoryItem } from '../services/api';
import { Image as ImageIcon, Video, Search, Filter, Trash2, AlertTriangle, Clock, ChevronDown, X, ArrowUpDown, Download, Share2, FileText, BarChart3 } from 'lucide-react';

const TYPE_ICONS = { Image: ImageIcon, Video: Video };
const TYPE_COLORS = {
  Image: 'text-accent bg-accent/10 border-accent/30',
  Video: 'text-accent bg-accent/10 border-accent/30',
};
const VERDICT_COLORS = {
  'Authentic': 'text-success',
  'Likely Authentic': 'text-success',
  'Suspicious': 'text-warning',
  'Likely AI Generated': 'text-warning',
  'AI Generated': 'text-danger',
  'Deepfake': 'text-danger',
  'Manipulated': 'text-danger',
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
  const [sortBy, setSortBy]         = useState('date');
  const [sortOrder, setSortOrder]   = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = 10;

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

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleExport = (format) => {
    // Simulate export
    console.log(`Exporting history as ${format}`);
  };

  const filtered = items.filter(item => {
    const matchType    = typeFilter === 'All' || item.type === typeFilter;
    const matchVerdict = verdictFilter === 'All' || (item.result || '').includes(verdictFilter);
    const matchSearch  = search === '' || (item.result || '').toLowerCase().includes(search.toLowerCase())
                       || (item.type || '').toLowerCase().includes(search.toLowerCase());
    return matchType && matchVerdict && matchSearch;
  });

  const sorted = [...filtered].sort((a, b) => {
    let comparison = 0;
    if (sortBy === 'date') {
      comparison = new Date(a.created_at) - new Date(b.created_at);
    } else if (sortBy === 'confidence') {
      comparison = (a.confidence || 0) - (b.confidence || 0);
    } else if (sortBy === 'verdict') {
      comparison = (a.result || '').localeCompare(b.result || '');
    }
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  const paginated = sorted.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const totalPages = Math.ceil(sorted.length / itemsPerPage);

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
    <div className="min-h-screen flex items-center justify-center pt-16 bg-background">
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-16 h-16 border-2 border-accent/30 border-t-accent rounded-full mx-auto mb-4 shadow-glow"
        />
        <p className="text-text-secondary">Loading history…</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen pt-24 px-4 pb-12 bg-background">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold font-display text-text-primary mb-1">Detection History</h1>
              <p className="text-text-secondary text-sm">All your previous content authenticity analyses</p>
            </div>
            <div className="flex gap-2">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleExport('csv')}
                className="px-4 py-2 bg-glass rounded-xl text-text-secondary hover:text-text-primary border border-card/50 flex items-center gap-2"
              >
                <Download className="w-4 h-4" /> Export
              </motion.button>
            </div>
          </div>
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-glass border-danger/30 rounded-xl text-danger text-sm mb-6 flex gap-2"
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
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search by type or verdict…"
                className="w-full pl-10 pr-4 py-2.5 bg-glass-dark rounded-xl text-text-primary placeholder:text-text-secondary/60 text-sm focus:border-accent/40 focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all border border-card/50"
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowFilters(p => !p)}
              className={`flex items-center gap-2 px-4 py-2.5 bg-glass-dark rounded-xl text-text-secondary text-sm hover:bg-card/50 transition-all border border-card/50 ${showFilters ? 'bg-accent/10 text-accent border-accent/30' : ''}`}
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
                <div className="bg-glass p-4 space-y-4 border border-card/50 rounded-xl">
                  <div>
                    <p className="text-text-secondary text-xs mb-2 uppercase tracking-wider">Type</p>
                    <div className="flex gap-2">
                      {['All', 'Image', 'Video'].map(t => (
                        <motion.button
                          key={t}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => setTypeFilter(t)}
                          className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${typeFilter === t ? 'bg-accent text-text-primary shadow-glow' : 'bg-glass text-text-secondary hover:text-text-primary border border-card/50'}`}
                        >
                          {t}
                        </motion.button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-text-secondary text-xs mb-2 uppercase tracking-wider">Verdict</p>
                    <div className="flex flex-wrap gap-2">
                      {['All', 'Authentic', 'Suspicious', 'AI Generated', 'Deepfake', 'Manipulated'].map(v => (
                        <motion.button
                          key={v}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => setVFilter(v)}
                          className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${verdictFilter === v ? 'bg-accent text-text-primary shadow-glow' : 'bg-glass text-text-secondary hover:text-text-primary border border-card/50'}`}
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

        {/* Sort Options */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex items-center gap-3 mb-4"
        >
          <span className="text-text-secondary text-sm">Sort by:</span>
          <div className="flex gap-2">
            {['date', 'confidence', 'verdict'].map(field => (
              <motion.button
                key={field}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleSort(field)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  sortBy === field
                    ? 'bg-accent text-white shadow-glow'
                    : 'bg-glass text-text-secondary hover:text-text-primary border border-card/50'
                }`}
              >
                {field.charAt(0).toUpperCase() + field.slice(1)}
                {sortBy === field && (
                  <ArrowUpDown className={`w-3 h-3 ${sortOrder === 'asc' ? 'rotate-180' : ''}`} />
                )}
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Summary */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex items-center justify-between mb-4"
        >
          <span className="text-text-secondary text-sm">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
          {(search || typeFilter !== 'All' || verdictFilter !== 'All') && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => { setSearch(''); setTypeFilter('All'); setVFilter('All'); }}
              className="flex items-center gap-1 text-accent text-xs hover:underline"
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
            className="text-center py-20 bg-glass rounded-2xl border border-card/50"
          >
            <Clock className="w-16 h-16 text-text-secondary/30 mx-auto mb-4" />
            <p className="text-text-secondary">
              {items.length === 0 ? 'No analyses yet. Start detecting content!' : 'No results match your filters.'}
            </p>
          </motion.div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {paginated.map((item, i) => {
                const Icon = TYPE_ICONS[item.type] || ImageIcon;
                const typeStyle = TYPE_COLORS[item.type] || 'text-text-secondary bg-glass border-card/50';
                const vColor = Object.entries(VERDICT_COLORS).find(([k]) => (item.result || '').includes(k))?.[1] || 'text-text-secondary';
                return (
                  <motion.div
                    key={item.analysis_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20, height: 0 }}
                    transition={{ delay: i * 0.05 }}
                    whileHover={{ scale: 1.01, x: 4 }}
                    className="flex items-center gap-4 p-4 bg-glass rounded-xl cursor-pointer group border border-card/50"
                  >
                    {/* Type icon */}
                    <motion.div
                      whileHover={{ scale: 1.1, rotate: 5 }}
                      className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border ${typeStyle} shadow-glow`}
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
                      <p className="text-text-secondary text-xs">{fmtDate(item.created_at)}</p>
                    </div>

                    {/* Confidence */}
                    <div className="text-right shrink-0">
                      <p className="text-text-primary font-bold text-sm font-display">{fmt(item.confidence)}</p>
                      <p className="text-text-secondary text-xs">confidence</p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        className="p-2 bg-glass text-text-secondary hover:text-accent hover:bg-accent/10 rounded-lg transition border border-card/50"
                        title="View Details"
                      >
                        <FileText className="w-4 h-4" />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        className="p-2 bg-glass text-text-secondary hover:text-accent hover:bg-accent/10 rounded-lg transition border border-card/50"
                        title="Share"
                      >
                        <Share2 className="w-4 h-4" />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => handleDelete(item.analysis_id)}
                        disabled={deleting === item.analysis_id}
                        className="p-2 bg-glass text-text-secondary hover:text-danger hover:bg-danger/10 rounded-lg transition disabled:opacity-50 border border-card/50"
                        title="Delete"
                      >
                        {deleting === item.analysis_id
                          ? <div className="w-4 h-4 border border-danger/50 border-t-danger rounded-full animate-spin" />
                          : <Trash2 className="w-4 h-4" />
                        }
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="flex items-center justify-center gap-2 mt-6"
          >
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-glass rounded-xl text-text-secondary hover:text-text-primary border border-card/50 disabled:opacity-50"
            >
              Previous
            </motion.button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <motion.button
                key={page}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setCurrentPage(page)}
                className={`w-10 h-10 rounded-xl font-medium transition-all ${
                  currentPage === page
                    ? 'bg-accent text-white shadow-glow'
                    : 'bg-glass text-text-secondary hover:text-text-primary border border-card/50'
                }`}
              >
                {page}
              </motion.button>
            ))}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-glass rounded-xl text-text-secondary hover:text-text-primary border border-card/50 disabled:opacity-50"
            >
              Next
            </motion.button>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default History;
