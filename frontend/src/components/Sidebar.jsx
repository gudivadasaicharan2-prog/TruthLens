import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, 
  History, 
  Zap, 
  Settings, 
  Info, 
  Github,
  Menu,
  X,
  Eye,
  Shield
} from 'lucide-react';

/**
 * Modern Sidebar Component
 * Features:
 * - TruthLens Logo
 * - AI Image Forensics branding
 * - Navigation with active state
 * - Professional hover animations
 * - Responsive design
 */
const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  
  const navItems = [
    { icon: Home, label: 'Home', path: '/', enabled: true },
    { icon: Eye, label: 'Detect', path: '/detect', enabled: true },
    { icon: Zap, label: 'Dashboard', path: '/dashboard', enabled: true },
    { icon: History, label: 'History', path: '/history', enabled: true },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <>
      {/* Mobile backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={{ x: -320 }}
        animate={{ x: isOpen ? 0 : -320 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className={`
          fixed top-0 left-0 z-50 h-screen w-80
          glass border-r border-white/10
          lg:static lg:translate-x-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:block
        `}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center justify-between">
              <Link to="/" className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white font-['Space_Grotesk']">
                    TruthLens
                  </h1>
                  <p className="text-xs text-gray-400">AI Image Forensics</p>
                </div>
              </Link>
              
              <button
                onClick={onClose}
                className="lg:hidden p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => item.enabled && onClose()}
                  className={`
                    relative flex items-center gap-3 px-4 py-3 rounded-xl
                    transition-all duration-200 group
                    ${item.enabled 
                      ? active 
                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' 
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                      : 'text-gray-600 cursor-not-allowed opacity-50'
                    }
                  `}
                >
                  {active && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="absolute inset-0 bg-blue-500/20 rounded-xl border border-blue-500/30"
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                  
                  <Icon className={`w-5 h-5 relative z-10 ${active ? 'text-blue-400' : ''}`} />
                  <span className="relative z-10 font-medium">{item.label}</span>
                  
                  {!item.enabled && (
                    <span className="ml-auto text-xs text-gray-600">Soon</span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-white/10 space-y-2">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all duration-200 group"
            >
              <Github className="w-5 h-5" />
              <span className="font-medium">GitHub</span>
            </a>
            
            <div className="px-4 py-3 rounded-xl bg-white/5 border border-white/10">
              <p className="text-xs text-gray-400">
                Version <span className="text-white font-medium">v6.0</span>
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Configurable Fusion Engine
              </p>
            </div>
          </div>
        </div>
      </motion.aside>
    </>
  );
};

export default Sidebar;
