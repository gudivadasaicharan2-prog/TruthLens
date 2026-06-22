import { useNavigate, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';
import { Shield, LayoutDashboard, History, Scan, LogOut, User, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Navbar = () => {
  const { user, logoutUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
    setDropdownOpen(false);
  };

  const navLinks = [
    { path: '/', label: 'Home' },
    { path: '/detect', label: 'Detect' },
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/history', label: 'History' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050d1a]/90 backdrop-blur-xl border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">

        {/* Logo */}
        <div
          className="flex items-center gap-2 cursor-pointer group"
          onClick={() => navigate('/')}
        >
          <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <span className="text-white font-bold text-xl font-['Space_Grotesk'] group-hover:text-cyan-400 transition-colors">
            TruthLens
          </span>
        </div>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map(({ path, label }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive(path)
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Right: Theme + User */}
        <div className="flex items-center gap-3">
          <ThemeToggle />

          {user ? (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 bg-white/8 hover:bg-white/15 transition px-3 py-2 rounded-xl border border-white/10"
              >
                {user.picture ? (
                  <img src={user.picture} alt={user.name} className="w-7 h-7 rounded-full object-cover" />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm">
                    {user.name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                )}
                <span className="text-white text-sm font-medium max-w-[100px] truncate hidden sm:block">
                  {user.name || user.email}
                </span>
                <span className="text-gray-400 text-xs">▾</span>
              </button>

              <AnimatePresence>
                {dropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.95 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-13 mt-1 w-52 bg-[#0a1628] border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-50"
                  >
                    <div className="px-4 py-3 border-b border-white/10">
                      <p className="text-white text-sm font-medium truncate">{user.name}</p>
                      <p className="text-gray-400 text-xs truncate">{user.email}</p>
                      <span className="inline-block mt-1 px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded-full capitalize">
                        {user.role || 'user'}
                      </span>
                    </div>
                    {[
                      { icon: User, label: 'My Profile', path: '/profile' },
                      { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
                      { icon: History, label: 'History', path: '/history' },
                    ].map(({ icon: Icon, label, path }) => (
                      <button
                        key={path}
                        onClick={() => { navigate(path); setDropdownOpen(false); }}
                        className="w-full flex items-center gap-3 text-left px-4 py-2.5 text-gray-300 hover:bg-white/5 text-sm transition"
                      >
                        <Icon className="w-4 h-4 text-gray-500" /> {label}
                      </button>
                    ))}
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 text-left px-4 py-2.5 text-red-400 hover:bg-red-500/10 text-sm transition border-t border-white/10"
                    >
                      <LogOut className="w-4 h-4" /> Logout
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/login')}
                className="text-gray-300 hover:text-white text-sm px-4 py-2 transition"
              >
                Login
              </button>
              <button
                onClick={() => navigate('/register')}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:opacity-90 text-white font-semibold text-sm px-4 py-2 rounded-xl transition"
              >
                Get Started
              </button>
            </div>
          )}

          {/* Mobile menu toggle */}
          <button
            className="md:hidden p-2 text-gray-400 hover:text-white"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-white/10 bg-[#050d1a] overflow-hidden"
          >
            <div className="px-4 py-3 space-y-1">
              {navLinks.map(({ path, label }) => (
                <button
                  key={path}
                  onClick={() => { navigate(path); setMobileOpen(false); }}
                  className={`w-full text-left px-4 py-2 rounded-lg text-sm font-medium transition ${
                    isActive(path) ? 'bg-cyan-500/15 text-cyan-400' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
