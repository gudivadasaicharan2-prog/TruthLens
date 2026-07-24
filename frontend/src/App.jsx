import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useState, lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import Background from './components/Background';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// Lazy load pages for better performance
const Landing = lazy(() => import('./pages/Landing'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Detect = lazy(() => import('./pages/Detect'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));
const History = lazy(() => import('./pages/History'));
const Results = lazy(() => import('./pages/Results'));
const NotFound = lazy(() => import('./pages/NotFound'));

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--background)' }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-16 h-16 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full ring-glow"
        />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" />;
  return children;
};

const PageTransition = ({ children }) => {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
};

const NavbarLayout = ({ children, onMenuToggle, isMenuOpen }) => (
  <PageTransition>
    <Navbar onMenuToggle={onMenuToggle} isMenuOpen={isMenuOpen} />
    <main className="min-h-screen pt-16">
      {children}
    </main>
  </PageTransition>
);

const App = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const LoadingFallback = () => (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--background)' }}>
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-16 h-16 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full mx-auto mb-4 ring-glow"
        />
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );

  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <div className="min-h-screen transition-colors duration-300" style={{ background: 'var(--background)' }}>
            <Background />
            
            <Suspense fallback={<LoadingFallback />}>
              <Routes>
                <Route path="/" element={<PageTransition><Landing /></PageTransition>} />
                <Route path="/login" element={<PageTransition><Login /></PageTransition>} />
                <Route path="/register" element={<PageTransition><Register /></PageTransition>} />
                <Route path="/detect" element={
                  <NavbarLayout onMenuToggle={() => setSidebarOpen(!sidebarOpen)} isMenuOpen={sidebarOpen}>
                    <Detect />
                  </NavbarLayout>
                } />
                <Route path="/dashboard" element={
                  <NavbarLayout onMenuToggle={() => setSidebarOpen(!sidebarOpen)} isMenuOpen={sidebarOpen}>
                    <Dashboard />
                  </NavbarLayout>
                } />
                <Route path="/history" element={
                  <NavbarLayout onMenuToggle={() => setSidebarOpen(!sidebarOpen)} isMenuOpen={sidebarOpen}>
                    <History />
                  </NavbarLayout>
                } />
                <Route path="/results" element={
                  <NavbarLayout onMenuToggle={() => setSidebarOpen(!sidebarOpen)} isMenuOpen={sidebarOpen}>
                    <Results />
                  </NavbarLayout>
                } />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <NavbarLayout onMenuToggle={() => setSidebarOpen(!sidebarOpen)} isMenuOpen={sidebarOpen}>
                        <Profile />
                      </NavbarLayout>
                    </ProtectedRoute>
                  }
                />
                <Route path="*" element={<PageTransition><NotFound /></PageTransition>} />
              </Routes>
            </Suspense>
          </div>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
