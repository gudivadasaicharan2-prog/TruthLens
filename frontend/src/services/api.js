import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'https://truthlens-htjy.onrender.com';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
});

// ── Request interceptor — attach token + user email header ────────────────────
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;

  // Send user email as a fallback header so backend can scope data
  // even when using mock hash tokens that can't be decoded server-side
  try {
    const raw = localStorage.getItem('user');
    if (raw && raw !== 'undefined') {
      const user = JSON.parse(raw);
      if (user?.email) config.headers['X-User-Email'] = user.email;
    }
  } catch (_) { /* ignore */ }

  return config;
});

// ── Response interceptor ──────────────────────────────────────────────────────
api.interceptors.response.use(
  res => {
    console.log("Response Status:", res.status);
    console.log("Response Body:", res.data);
    return res;
  },
  err => {
    if (err.response) {
      console.log("Response Status:", err.response.status);
      console.log("Response Body:", err.response.data);
    }
    if (err.code === 'ECONNABORTED') {
      console.error('[API] TIMEOUT:', err.config?.url);
    } else if (err.code === 'ERR_NETWORK' || err.message === 'Network Error') {
      console.error('[API] NETWORK ERROR — backend may be down:', err.config?.url);
    } else if (err.response) {
      console.error(`[API] HTTP ${err.response.status} — ${err.config?.url}`, err.response.data);
    }
    return Promise.reject(err);
  }
);

export const getErrorMessage = (err) => {
  if (err.code === 'ECONNABORTED' || err.message?.includes('timeout'))
    return 'Request timed out. Please try again.';
  if (err.code === 'ERR_NETWORK' || err.message === 'Network Error')
    return 'Backend unavailable';
  if (err.response?.status === 404)
    return 'Invalid API endpoint';
  const body = err.response?.data;
  if (body?.detail) return typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
  if (body?.message) return body.message;
  if (err.response?.status) return `Server returned HTTP ${err.response.status}`;
  return err.message || 'An unexpected error occurred.';
};

// ── Auth ──────────────────────────────────────────────────────────────────────
export const register = (name, email, password, role) =>
  api.post('/api/v1/auth/register', { name, email, password, role });

export const login = (email, password) =>
  api.post('/api/v1/auth/login', { email, password });

export const googleLogin = (token) =>
  api.post('/api/v1/auth/google', { token });

// ── Image ─────────────────────────────────────────────────────────────────────
export const analyzeImage = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/v1/image/analyze', formData, {
    timeout: 120000,
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(res => res.data);
};

// ── Video ─────────────────────────────────────────────────────────────────────
export const analyzeVideo = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const apiUrl = '/api/v1/video/analyze';
  console.log('[VIDEO] File:', file.name, `(${(file.size / 1024 / 1024).toFixed(2)} MB)`, file.type);
  console.log('[VIDEO] Uploading to:', apiUrl);

  try {
    const response = await api.post(apiUrl, formData, {
      timeout: 300000,
      // Do NOT set Content-Type — let browser set multipart boundary
    });
    console.log('[VIDEO] Response status:', response.status);
    console.log('[VIDEO] Response data:', response.data);
    return response.data;
  } catch (error) {
    console.error('[VIDEO] Upload/analysis error:', error);
    if (error.response) {
      console.error('[VIDEO] HTTP status:', error.response.status);
      console.error('[VIDEO] Response body:', error.response.data);
    }
    throw error;
  }
};

// ── Audio ─────────────────────────────────────────────────────────────────────
export const analyzeAudio = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/v1/audio/analyze', formData, {
    timeout: 120000,
  }).then(res => res.data);
};

// Helper to get current UID
const getUid = () => {
  try {
    const raw = localStorage.getItem('user');
    if (raw && raw !== 'undefined') {
      const user = JSON.parse(raw);
      if (user?.user_id) return user.user_id;
    }
  } catch (_) { /* ignore */ }
  return 'unauthorized';
};

const logBeforeCall = (url) => {
  try {
    const rawUser = localStorage.getItem('user');
    const user = rawUser && rawUser !== 'undefined' ? JSON.parse(rawUser) : null;
    const token = localStorage.getItem('token');
    console.log("Current User:", user);
    console.log("UID:", user?.user_id);
    console.log("Token:", token);
    if (url.includes('statistics') || url.includes('daily') || url.includes('recent') || url.includes('topics')) {
      console.log("Dashboard Request URL:", url);
    }
    if (url.includes('history')) {
      console.log("History Request URL:", url);
    }
  } catch(e) {}
};

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getDashboardStats = () => { const url = `/api/v1/users/${getUid()}/statistics`; logBeforeCall(url); return api.get(url); };
export const getDailyStats     = () => { const url = `/api/v1/users/${getUid()}/daily`; logBeforeCall(url); return api.get(url); };
export const getRecentActivity = () => { const url = `/api/v1/users/${getUid()}/recent`; logBeforeCall(url); return api.get(url); };
export const getTopDetections  = () => { const url = `/api/v1/users/${getUid()}/topics`; logBeforeCall(url); return api.get(url); };

// ── User / History ────────────────────────────────────────────────────────────
export const getUserHistory    = ()   => { const url = `/api/v1/users/${getUid()}/history`; logBeforeCall(url); return api.get(url); };
export const deleteHistoryItem = (id) => { const url = `/api/v1/users/${getUid()}/history/${id}`; logBeforeCall(url); return api.delete(url); };
export const getUserProfile    = ()   => { const url = `/api/v1/users/${getUid()}/profile`; logBeforeCall(url); return api.get(url); };

export default api;
