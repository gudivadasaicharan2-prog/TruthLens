import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

// ── JWT expiry check ───────────────────────────────────────────────────────────
const isTokenExpired = (token) => {
  if (!token) return true;
  try {
    // Decode payload (works for both real JWT and Google credential JWTs)
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (!payload.exp) return false; // No expiry = never expires (mock hash tokens)
    return Date.now() / 1000 > payload.exp;
  } catch (_) {
    // Not a JWT (mock hash token) — treat as valid
    return false;
  }
};

// ── Normalize user object ──────────────────────────────────────────────────────
// Ensures consistent shape regardless of login method (email vs Google)
const normalizeUser = (userData) => {
  if (!userData) return null;
  return {
    user_id:    userData.user_id    || userData.sub   || '',
    name:       userData.name       || userData.email?.split('@')[0] || 'User',
    email:      userData.email      || '',
    picture:    userData.picture    || userData.photoURL || '',
    role:       userData.role       || 'general',
    provider:   userData.provider   || 'email',
    created_at: userData.created_at || '',
    last_login: userData.last_login || new Date().toISOString(),
  };
};

export const AuthProvider = ({ children }) => {
  const [user, setUser]       = useState(null);
  const [token, setToken]     = useState(null);
  const [loading, setLoading] = useState(true);

  // ── Restore session on mount ────────────────────────────────────────────────
  useEffect(() => {
    try {
      const savedToken = localStorage.getItem('token');
      const savedUser  = localStorage.getItem('user');

      if (savedToken && savedUser && savedUser !== 'undefined') {
        if (isTokenExpired(savedToken)) {
          // Token expired — clear and force re-login
          console.log('[AUTH] Token expired, clearing session');
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        } else {
          const parsed = JSON.parse(savedUser);
          setToken(savedToken);
          setUser(normalizeUser(parsed));
        }
      }
    } catch (e) {
      console.error('[AUTH] Session restore failed:', e);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Login ───────────────────────────────────────────────────────────────────
  const loginUser = useCallback((tokenValue, userData) => {
    const normalized = normalizeUser(userData);
    localStorage.setItem('token', tokenValue);
    localStorage.setItem('user', JSON.stringify(normalized));
    setToken(tokenValue);
    setUser(normalized);
    console.log('[AUTH] Logged in:', normalized.email, '| provider:', normalized.provider);
  }, []);

  // ── Logout ──────────────────────────────────────────────────────────────────
  const logoutUser = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    console.log('[AUTH] Logged out');
  }, []);

  const isAuthenticated = Boolean(user && token);

  return (
    <AuthContext.Provider value={{ user, token, loginUser, logoutUser, loading, isAuthenticated }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
