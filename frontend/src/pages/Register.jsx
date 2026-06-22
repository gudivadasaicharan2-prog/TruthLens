import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, User, Mail, Lock, Eye, EyeOff, ArrowRight, CheckCircle2, Briefcase, GraduationCap, Building2 } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import { useAuth } from '../context/AuthContext';
import ToastNotification from '../components/ToastNotification';
import { register, googleLogin } from '../services/api';

const Register = () => {
  const navigate = useNavigate();
  const { loginUser } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'general',
    agreeTerms: false
  });
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({ name: '', email: '', password: '', confirmPassword: '', agreeTerms: '' });
  const [passwordStrength, setPasswordStrength] = useState(0);

  const calculatePasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (password.match(/[a-z]/)) strength += 25;
    if (password.match(/[A-Z]/)) strength += 25;
    if (password.match(/[0-9]/)) strength += 25;
    return strength;
  };

  const validateForm = () => {
    const newErrors = { name: '', email: '', password: '', confirmPassword: '', agreeTerms: '' };
    let isValid = true;

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
      isValid = false;
    } else if (formData.name.length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
      isValid = false;
    }

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
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
      isValid = false;
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
      isValid = false;
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
      isValid = false;
    }

    if (!formData.agreeTerms) {
      newErrors.agreeTerms = 'You must agree to the terms';
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
      console.log("Registering user:", formData);
      const res = await register(formData.name, formData.email, formData.password, formData.role);
      loginUser(res.data.access_token || 'registered', res.data.user);
      setToast({ message: 'Registration successful! Redirecting to login...', type: 'success' });
      setTimeout(() => navigate('/login'), 1500);
    } catch (error) {
      console.error("Registration error:", error);
      console.error("Error response:", error.response?.data);
      console.error("Error message:", error.message);
      const errorMsg = error.response?.data?.detail || error.message || 'Registration failed. Is the backend running?';
      setToast({ message: errorMsg, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const decoded = jwtDecode(credentialResponse.credential);
      console.log("Google user:", decoded);
      
      // Send Google token to backend
      const res = await googleLogin(credentialResponse.credential);
      const data = res.data;
      loginUser(data.access_token, data.user);
      setToast({ message: 'Google login successful! Redirecting...', type: 'success' });
      setTimeout(() => navigate('/detect'), 1500);
    } catch (error) {
      console.error('Google login error:', error);
      setToast({ message: 'Google login failed. Please try again.', type: 'error' });
    }
  };

  const handleGoogleError = () => {
    setToast({ message: 'Google login failed. Please try again.', type: 'error' });
  };

  const roles = [
    { value: 'general', label: 'General User', icon: User, desc: 'Standard access to all features' },
    { value: 'journalist', label: 'Journalist', icon: Briefcase, desc: 'Professional verification tools' },
    { value: 'student', label: 'Student', icon: GraduationCap, desc: 'Educational resources included' },
    { value: 'government', label: 'Government', icon: Building2, desc: 'Enterprise-grade security' },
  ];

  return (
    <div className="min-h-screen bg-navy-900 bg-hex-pattern flex items-center justify-center px-4 py-12 relative overflow-hidden">
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
        className="w-full max-w-2xl relative z-10"
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
            <h1 className="text-4xl font-heading font-bold text-text-primary mb-2">Create Account</h1>
            <p className="text-text-secondary text-center">Join TruthLens and start detecting misinformation</p>
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
            <span className="text-text-secondary text-sm">or register with email</span>
            <div className="flex-1 h-px bg-navy-700"></div>
          </div>

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">Full Name</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className={`w-full pl-12 pr-4 py-3 bg-navy-900 border ${errors.name ? 'border-red-500' : 'border-navy-700'} rounded-xl text-text-primary focus:border-cyan-400 focus:outline-none transition-colors`}
                    placeholder="John Doe"
                    required
                  />
                </div>
                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
              </div>

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
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => {
                      setFormData({ ...formData, password: e.target.value });
                      setPasswordStrength(calculatePasswordStrength(e.target.value));
                    }}
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
                {formData.password && (
                  <div className="mt-2">
                    <div className="flex gap-1 mb-1">
                      {[...Array(4)].map((_, i) => (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded-full ${
                            i < passwordStrength / 25
                              ? passwordStrength < 50
                                ? 'bg-red-500'
                                : passwordStrength < 75
                                ? 'bg-yellow-500'
                                : 'bg-green-500'
                              : 'bg-navy-700'
                          }`}
                        ></div>
                      ))}
                    </div>
                    <p className="text-xs text-text-secondary">
                      {passwordStrength < 25 ? 'Weak' : passwordStrength < 50 ? 'Fair' : passwordStrength < 75 ? 'Good' : 'Strong'}
                    </p>
                  </div>
                )}
                {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    className={`w-full pl-12 pr-12 py-3 bg-navy-900 border ${errors.confirmPassword ? 'border-red-500' : 'border-navy-700'} rounded-xl text-text-primary focus:border-cyan-400 focus:outline-none transition-colors`}
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-cyan-400 transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {errors.confirmPassword && <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-3">Select Your Role</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {roles.map((role) => (
                  <button
                    key={role.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, role: role.value })}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      formData.role === role.value
                        ? 'border-cyan-500 bg-cyan-500/10'
                        : 'border-navy-700 bg-navy-900 hover:border-cyan-500/50'
                    }`}
                  >
                    <role.icon className={`w-6 h-6 mx-auto mb-2 ${formData.role === role.value ? 'text-cyan-400' : 'text-gray-500'}`} />
                    <div className={`text-sm font-medium ${formData.role === role.value ? 'text-cyan-400' : 'text-text-primary'}`}>
                      {role.label}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.agreeTerms}
                  onChange={(e) => setFormData({ ...formData, agreeTerms: e.target.checked })}
                  className="w-5 h-5 mt-0.5 rounded border-navy-700 bg-navy-900 text-cyan-400 focus:ring-cyan-400 focus:ring-offset-0"
                />
                <span className="text-sm text-text-secondary">
                  I agree to the{' '}
                  <Link to="/terms" className="text-cyan-400 hover:text-cyan-300 transition-colors">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link to="/privacy" className="text-cyan-400 hover:text-cyan-300 transition-colors">
                    Privacy Policy
                  </Link>
                </span>
              </label>
              {errors.agreeTerms && <p className="text-red-500 text-sm mt-1">{errors.agreeTerms}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-cyan-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Creating account...
                </>
              ) : (
                <>
                  Create Account <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Sign In Link */}
          <div className="mt-8 text-center">
            <p className="text-text-secondary">
              Already have an account?{' '}
              <Link to="/login" className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors inline-flex items-center gap-1">
                Sign In <ArrowRight className="w-4 h-4" />
              </Link>
            </p>
          </div>

          {/* Trust Badge */}
          <div className="mt-8 pt-6 border-t border-navy-700">
            <div className="flex items-center justify-center gap-2 text-text-secondary text-sm">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span>Your data is protected with enterprise-grade encryption</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Register;
