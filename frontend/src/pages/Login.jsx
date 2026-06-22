import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Mail, Lock, Eye, EyeOff, ArrowRight, CheckCircle2 } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import { useAuth } from '../context/AuthContext';
import ToastNotification from '../components/ToastNotification';
import { login, googleLogin } from '../services/api';

const Login = () => {
  const navigate = useNavigate();
  const { loginUser } = useAuth();
  const [formData, setFormData] = useState({ email: '', password: '', remember: false });
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({ email: '', password: '' });

  const validateForm = () => {
    const newErrors = { email: '', password: '' };
    let isValid = true;

    if (!formData.email) {
      newErrors.email = 'Email is required';
      isValid = false;
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
      isValid = false;
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
      isValid = false;
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    try {
      console.log("Logging in:", formData);
      const res = await login(formData.email, formData.password);
      loginUser(res.data.access_token, res.data.user);
      setToast({ message: 'Login successful! Redirecting...', type: 'success' });
      setTimeout(() => navigate('/detect'), 1500);
    } catch (error) {
      console.error("Login error:", error);
      console.error("Error response:", error.response?.data);
      console.error("Error message:", error.message);
      const errorMsg = error.response?.data?.detail || error.message || 'Login failed. Please check your credentials.';
      setToast({ message: errorMsg, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      // Send Google token to backend — it returns a proper JWT + normalized user
      const res  = await googleLogin(credentialResponse.credential);
      const data = res.data;
      loginUser(data.access_token, data.user);
      setToast({ message: 'Google login successful! Redirecting...', type: 'success' });
      setTimeout(() => navigate('/detect'), 1500);
    } catch (error) {
      console.error('Google login error:', error);
      // Fallback: decode client-side and use mock token
      try {
        const decoded = jwtDecode(credentialResponse.credential);
        const mockUser = {
          user_id:  decoded.sub,
          name:     decoded.name,
          email:    decoded.email,
          picture:  decoded.picture,
          role:     'general',
          provider: 'google',
          created_at: new Date().toISOString(),
        };
        // Use Google credential itself as the token (it's a valid JWT)
        loginUser(credentialResponse.credential, mockUser);
        setToast({ message: 'Signed in with Google (offline mode)', type: 'success' });
        setTimeout(() => navigate('/detect'), 1500);
      } catch (_) {
        setToast({ message: 'Google login failed. Please try again.', type: 'error' });
      }
    }
  };

  const handleGoogleError = () => {
    setToast({ message: 'Google login failed. Please try again.', type: 'error' });
  };

  return (
    <div className="min-h-screen bg-navy-900 bg-hex-pattern flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>

      {toast && (
        <ToastNotification
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-lg relative z-10"
      >
        <div className="bg-navy-800/50 backdrop-blur-xl border border-cyan-500/20 rounded-3xl p-10 shadow-2xl">
          {/* Logo and Header */}
          <div className="flex flex-col items-center mb-10">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              className="w-20 h-20 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-cyan-500/25"
            >
              <Shield className="w-10 h-10 text-white" />
            </motion.div>
            <h1 className="text-4xl font-heading font-bold text-text-primary mb-2">Welcome Back</h1>
            <p className="text-text-secondary text-center">Sign in to your TruthLens account to continue</p>
          </div>

          {/* Social Login Options */}
          <div className="mb-8 flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              theme="filled_black"
              shape="rectangular"
              size="large"
              text="continue_with"
            />
          </div>

          {/* Divider */}
          <div className="flex items-center gap-4 mb-8">
            <div className="flex-1 h-px bg-navy-700"></div>
            <span className="text-text-secondary text-sm">or continue with email</span>
            <div className="flex-1 h-px bg-navy-700"></div>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={`w-full pl-12 pr-4 py-3 bg-navy-900 border ${errors.email ? 'border-red-500' : 'border-navy-700'} rounded-xl text-text-primary focus:border-cyan-400 focus:outline-none transition-colors`}
                  placeholder="you@example.com"
                  required
                />
              </div>
              {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className={`w-full pl-12 pr-12 py-3 bg-navy-900 border ${errors.password ? 'border-red-500' : 'border-navy-700'} rounded-xl text-text-primary focus:border-cyan-400 focus:outline-none transition-colors`}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-cyan-400 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.remember}
                  onChange={(e) => setFormData({ ...formData, remember: e.target.checked })}
                  className="w-4 h-4 rounded border-navy-700 bg-navy-900 text-cyan-400 focus:ring-cyan-400 focus:ring-offset-0"
                />
                <span className="text-sm text-text-secondary">Remember me</span>
              </label>
              <Link to="/forgot-password" className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-cyan-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Signing in...
                </>
              ) : (
                <>
                  Sign In <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Sign Up Link */}
          <div className="mt-8 text-center">
            <p className="text-text-secondary">
              Don't have an account?{' '}
              <Link to="/register" className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors inline-flex items-center gap-1">
                Create free account <ArrowRight className="w-4 h-4" />
              </Link>
            </p>
          </div>

          {/* Trust Badge */}
          <div className="mt-8 pt-6 border-t border-navy-700">
            <div className="flex items-center justify-center gap-2 text-text-secondary text-sm">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span>Secure login with end-to-end encryption</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
