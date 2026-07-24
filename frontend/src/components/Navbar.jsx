import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Bell, User, LogOut, Menu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Badge from './ui/Badge';

/**
 * Modern Top Navbar Component
 * Features:
 * - TruthLens branding with version badge
 * - Theme toggle
 * - Notification icon
 * - Profile dropdown
 * - Mobile menu toggle
 */
const Navbar = ({ onMenuToggle, isMenuOpen }) => {
  const { user, logoutUser } = useAuth();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
    setDropdownOpen(false);
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-40 glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 lg:px-6 flex items-center justify-between h-16">

        {/* Left: Mobile menu toggle + Logo */}
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuToggle}
            className="lg:hidden p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => navigate('/')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold text-white font-['Space_Grotesk'] group-hover:text-blue-400 transition-colors">
                TruthLens
              </h1>
              <div className="flex items-center gap-2">
                <Badge variant="primary" size="sm">v6.0</Badge>
                <span className="text-xs text-gray-400">Fusion Engine</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-1">
            <button
              onClick={() => navigate('/')}
              className="text-gray-300 hover:text-white text-sm px-3 py-2 transition-colors"
            >
              Home
            </button>
            <button
              onClick={() => navigate('/detect')}
              className="text-gray-300 hover:text-white text-sm px-3 py-2 transition-colors"
            >
              Detect
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-300 hover:text-white text-sm px-3 py-2 transition-colors"
            >
              Dashboard
            </button>
            <button
              onClick={() => navigate('/history')}
              className="text-gray-300 hover:text-white text-sm px-3 py-2 transition-colors"
            >
              History
            </button>
            <button
              onClick={() => navigate('/results')}
              className="text-gray-300 hover:text-white text-sm px-3 py-2 transition-colors"
            >
              Results
            </button>
          </div>

          {/* Notifications */}
          <button className="relative p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full" />
          </button>

          {/* User Menu */}
          {user ? (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 bg-white/5 hover:bg-white/10 transition px-3 py-2 rounded-xl border border-white/10"
              >
                {user.picture ? (
                  <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full object-cover ring-2 ring-white/10" />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm ring-2 ring-white/10">
                    {user.name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                )}
                <span className="text-white text-sm font-medium max-w-[120px] truncate hidden lg:block">
                  {user.name || user.email}
                </span>
              </button>

              <AnimatePresence>
                {dropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.95 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-14 mt-2 w-56 glass-card-xl overflow-hidden z-50"
                  >
                    <div className="px-4 py-3 border-b border-white/10">
                      <p className="text-white text-sm font-medium truncate">{user.name}</p>
                      <p className="text-gray-400 text-xs truncate">{user.email}</p>
                      <Badge variant="secondary" size="sm" className="mt-2">
                        {user.role || 'user'}
                      </Badge>
                    </div>
                    <div className="p-2">
                      {[
                        { icon: User, label: 'Profile', path: '/profile' },
                      ].map(({ icon: Icon, label, path }) => (
                        <button
                          key={path}
                          onClick={() => { navigate(path); setDropdownOpen(false); }}
                          className="w-full flex items-center gap-3 text-left px-3 py-2.5 text-gray-300 hover:text-white hover:bg-white/5 rounded-lg text-sm transition"
                        >
                          <Icon className="w-4 h-4 text-gray-500" /> {label}
                        </button>
                      ))}
                    </div>
                    <div className="p-2 border-t border-white/10">
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 text-left px-3 py-2.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg text-sm transition"
                      >
                        <LogOut className="w-4 h-4" /> Logout
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/login')}
                className="text-gray-300 hover:text-white text-sm px-4 py-2 transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={() => navigate('/register')}
                className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold text-sm px-4 py-2 rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/25"
              >
                Get Started
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
