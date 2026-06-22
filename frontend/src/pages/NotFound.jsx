import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Shield, Home } from 'lucide-react';

const NotFound = () => {
  return (
    <div className="min-h-screen bg-navy-900 bg-hex-pattern flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <Shield className="w-24 h-24 text-cyan-400 mx-auto mb-8" />
        <h1 className="text-6xl font-heading font-bold text-text-primary mb-4">404</h1>
        <p className="text-xl text-text-secondary mb-8">Page not found</p>
        <Link
          to="/"
          className="inline-flex items-center space-x-2 px-6 py-3 bg-cyan-400 text-navy-900 rounded-lg font-semibold hover:bg-cyan-500 transition-colors"
        >
          <Home className="w-5 h-5" />
          <span>Back to Home</span>
        </Link>
      </motion.div>
    </div>
  );
};

export default NotFound;
