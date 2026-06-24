import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://truthlens-htjy.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

// ── Request interceptor — attach token + user email header ────────────────────
api.interceptors.request.use(config => {
  console.log("API Base URL:", API_BASE_URL);
  console.log("Sending request to:", config.url);
  console.log("Request headers:", config.headers);
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
      console.error("HTTP Error:", err.response.status);
      console.error("Response:", err.response.data);
    } else if (err.request) {
      console.error("No response received:", err.request);
    } else {
      console.error("Request setup error:", err.message);
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
  api.post(`${API_BASE_URL}/api/v1/auth/register`, { name, email, password, role });

export const login = (email, password) =>
  api.post(`${API_BASE_URL}/api/v1/auth/login`, { email, password });

export const googleLogin = (token) =>
  api.post(`${API_BASE_URL}/api/v1/auth/google`, { token });

// ── Image ─────────────────────────────────────────────────────────────────────
export const analyzeImage = async (file) => {
  console.log("Selected file:", file);
  const formData = new FormData();
  formData.append('file', file);
  try {
    const API_BASE_URL = import.meta.env.VITE_API_URL || "https://truthlens-htjy.onrender.com";
    console.log("IMAGE REQUEST URL:", `${API_BASE_URL}/api/v1/image/analyze`);
    const response = await api.post(`${API_BASE_URL}/api/v1/image/analyze`, formData, {
      timeout: 120000,
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    console.log("API Response:", response);
    console.log("API Response Data:", response.data);
    console.log("Response Type:", typeof response.data);

    return response.data;
  } catch (error) {
    console.log("Caught Error:", error);
    throw error;
  }
};

// ── Video ─────────────────────────────────────────────────────────────────────
export const analyzeVideo = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const apiUrl = `${API_BASE_URL}/api/v1/video/analyze`;
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
  return api.post(`${API_BASE_URL}/api/v1/audio/analyze`, formData, {
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
  } catch (e) { }
};

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getDashboardStats = () => { const url = `${API_BASE_URL}/api/v1/users/${getUid()}/statistics`; logBeforeCall(url); return api.get(url); };
export const getDailyStats = () => { const url = `${API_BASE_URL}/api/v1/users/${getUid()}/daily`; logBeforeCall(url); return api.get(url); };
export const getRecentActivity = () => { const url = `${API_BASE_URL}/api/v1/users/${getUid()}/recent`; logBeforeCall(url); return api.get(url); };
export const getTopDetections = () => { const url = `${API_BASE_URL}/api/v1/users/${getUid()}/topics`; logBeforeCall(url); return api.get(url); };

// ── User / History ────────────────────────────────────────────────────────────
export const getUserHistory = () => { const url = `${API_BASE_URL}/api/v1/users/${getUid()}/history`; logBeforeCall(url); return api.get(url); };
export const deleteHistoryItem = (id) => { const url = `${API_BASE_URL}/api/v1/users/${getUid()}/history/${id}`; logBeforeCall(url); return api.delete(url); };
export const getUserProfile = () => { const url = `${API_BASE_URL}/api/v1/users/${getUid()}/profile`; logBeforeCall(url); return api.get(url); };

export default api;
