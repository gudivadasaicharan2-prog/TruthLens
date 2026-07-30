import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Info, Shield, Server, Zap, ChevronRight, Palette, Globe, Sliders, Download, Bell, Moon, Sun, ToggleLeft, ToggleRight } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

/**
 * Enhanced Settings Modal Component
 * 
 * Displays comprehensive app settings including theme, animations, language, confidence threshold, and auto-download options
 */
const Settings = ({ isOpen, onClose }) => {
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('preferences');
  const [settings, setSettings] = useState({
    animations: true,
    language: 'en',
    confidenceThreshold: 70,
    autoDownloadReports: false,
    notifications: true,
    highContrast: false
  });

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-3xl bg-card rounded-2xl border border-card/50 shadow-glow overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-card/50">
            <h2 className="text-xl font-bold text-text-primary">Settings</h2>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={onClose}
              className="p-2 rounded-lg bg-glass hover:bg-card/50 text-text-secondary transition-colors"
            >
              <X className="w-5 h-5" />
            </motion.button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-card/50">
            {['preferences', 'appearance', 'analysis', 'about'].map((tab) => (
              <motion.button
                key={tab}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 px-6 py-4 text-sm font-medium transition-all ${
                  activeTab === tab
                    ? 'text-accent border-b-2 border-accent bg-accent/5'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </motion.button>
            ))}
          </div>

          {/* Content */}
          <div className="p-6 max-h-[60vh] overflow-y-auto">
            <AnimatePresence mode="wait">
              {activeTab === 'preferences' && (
                <motion.div
                  key="preferences"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* Language */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-3">
                      <Globe className="w-5 h-5 text-accent" />
                      <h3 className="font-semibold text-text-primary">Language</h3>
                    </div>
                    <select
                      value={settings.language}
                      onChange={(e) => handleSettingChange('language', e.target.value)}
                      className="w-full px-4 py-2 bg-glass-dark rounded-lg text-text-primary border border-card/50 focus:border-accent/50 focus:outline-none"
                    >
                      <option value="en">English</option>
                      <option value="es">Español</option>
                      <option value="fr">Français</option>
                      <option value="de">Deutsch</option>
                      <option value="zh">中文</option>
                      <option value="ja">日本語</option>
                    </select>
                  </div>

                  {/* Notifications */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Bell className="w-5 h-5 text-accent" />
                        <div>
                          <h3 className="font-semibold text-text-primary">Notifications</h3>
                          <p className="text-text-secondary text-sm">Receive alerts for analysis completion</p>
                        </div>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => handleSettingChange('notifications', !settings.notifications)}
                        className="p-2"
                      >
                        {settings.notifications ? (
                          <ToggleRight className="w-6 h-6 text-accent" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-text-muted" />
                        )}
                      </motion.button>
                    </div>
                  </div>

                  {/* High Contrast */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Shield className="w-5 h-5 text-accent" />
                        <div>
                          <h3 className="font-semibold text-text-primary">High Contrast Mode</h3>
                          <p className="text-text-secondary text-sm">Increase contrast for better visibility</p>
                        </div>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => handleSettingChange('highContrast', !settings.highContrast)}
                        className="p-2"
                      >
                        {settings.highContrast ? (
                          <ToggleRight className="w-6 h-6 text-accent" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-text-muted" />
                        )}
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'appearance' && (
                <motion.div
                  key="appearance"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* Theme */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-3">
                      <Palette className="w-5 h-5 text-accent" />
                      <h3 className="font-semibold text-text-primary">Theme</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => theme === 'dark' ? null : toggleTheme()}
                        className={`p-4 rounded-xl border transition-all ${
                          theme === 'dark'
                            ? 'bg-accent/20 border-accent text-accent'
                            : 'bg-glass border-card/50 text-text-secondary hover:text-text-primary'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Moon className="w-5 h-5" />
                          <span className="font-medium">Dark</span>
                        </div>
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => theme === 'light' ? null : toggleTheme()}
                        className={`p-4 rounded-xl border transition-all ${
                          theme === 'light'
                            ? 'bg-accent/20 border-accent text-accent'
                            : 'bg-glass border-card/50 text-text-secondary hover:text-text-primary'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Sun className="w-5 h-5" />
                          <span className="font-medium">Light</span>
                        </div>
                      </motion.button>
                    </div>
                  </div>

                  {/* Animations */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Zap className="w-5 h-5 text-accent" />
                        <div>
                          <h3 className="font-semibold text-text-primary">Animations</h3>
                          <p className="text-text-secondary text-sm">Enable smooth transitions and effects</p>
                        </div>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => handleSettingChange('animations', !settings.animations)}
                        className="p-2"
                      >
                        {settings.animations ? (
                          <ToggleRight className="w-6 h-6 text-accent" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-text-muted" />
                        )}
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'analysis' && (
                <motion.div
                  key="analysis"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* Confidence Threshold */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-4">
                      <Sliders className="w-5 h-5 text-accent" />
                      <h3 className="font-semibold text-text-primary">Confidence Threshold</h3>
                    </div>
                    <div className="space-y-3">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={settings.confidenceThreshold}
                        onChange={(e) => handleSettingChange('confidenceThreshold', parseInt(e.target.value))}
                        className="w-full h-2 bg-card/50 rounded-lg appearance-none cursor-pointer accent-accent"
                      />
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">0%</span>
                        <span className="text-accent font-bold">{settings.confidenceThreshold}%</span>
                        <span className="text-text-secondary">100%</span>
                      </div>
                      <p className="text-text-secondary text-xs">
                        Minimum confidence level required for automatic verdict classification
                      </p>
                    </div>
                  </div>

                  {/* Auto Download Reports */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Download className="w-5 h-5 text-accent" />
                        <div>
                          <h3 className="font-semibold text-text-primary">Auto Download Reports</h3>
                          <p className="text-text-secondary text-sm">Automatically download PDF reports after analysis</p>
                        </div>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => handleSettingChange('autoDownloadReports', !settings.autoDownloadReports)}
                        className="p-2"
                      >
                        {settings.autoDownloadReports ? (
                          <ToggleRight className="w-6 h-6 text-accent" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-text-muted" />
                        )}
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'about' && (
                <motion.div
                  key="about"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-6"
                >
                  {/* Model Version */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-3">
                      <Shield className="w-5 h-5 text-accent" />
                      <h3 className="font-semibold text-text-primary">Model Version</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Architecture</span>
                        <span className="text-text-primary text-sm font-mono">EfficientNet-B4</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Version</span>
                        <span className="text-text-primary text-sm font-mono">v2.1.0</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Last Updated</span>
                        <span className="text-text-primary text-sm font-mono">2026-07-26</span>
                      </div>
                    </div>
                  </div>

                  {/* API Status */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-3">
                      <Server className="w-5 h-5 text-success" />
                      <h3 className="font-semibold text-text-primary">API Status</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-success shadow-glow-success animate-pulse" />
                      <span className="text-success text-sm font-medium">Operational</span>
                    </div>
                    <p className="text-text-secondary text-xs mt-2">All systems functioning normally</p>
                  </div>

                  {/* Performance */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-3">
                      <Zap className="w-5 h-5 text-warning" />
                      <h3 className="font-semibold text-text-primary">Performance</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Avg. Response Time</span>
                        <span className="text-text-primary text-sm font-mono">1.2s</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-text-secondary text-sm">Accuracy</span>
                        <span className="text-text-primary text-sm font-mono">94.7%</span>
                      </div>
                    </div>
                  </div>

                  {/* About */}
                  <div className="p-4 bg-glass rounded-xl border border-card/50">
                    <div className="flex items-center gap-3 mb-3">
                      <Info className="w-5 h-5 text-accent" />
                      <h3 className="font-semibold text-text-primary">About TruthLens</h3>
                    </div>
                    <p className="text-text-secondary text-sm leading-relaxed mb-3">
                      TruthLens is an AI-powered image authenticity detection platform that uses advanced machine learning models to identify AI-generated images, deepfakes, and manipulated content.
                    </p>
                    <div className="flex gap-2">
                      <a href="#" className="text-accent text-xs hover:underline">Privacy Policy</a>
                      <span className="text-text-muted text-xs">•</span>
                      <a href="#" className="text-accent text-xs hover:underline">Terms of Service</a>
                      <span className="text-text-muted text-xs">•</span>
                      <a href="#" className="text-accent text-xs hover:underline">Contact</a>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-card/50 bg-card/30 flex justify-between items-center">
            <p className="text-text-secondary text-xs">
              © 2026 TruthLens. All rights reserved.
            </p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onClose}
              className="px-6 py-2 bg-accent text-white rounded-xl font-medium shadow-glow"
            >
              Save Changes
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default Settings;
