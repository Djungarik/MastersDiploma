/**
 * Authentication Service
 * Handles API calls for login, register, and token management
 */

const TOKEN_KEY = "adaptive_ost_token";
const USER_KEY = "adaptive_ost_user";

/**
 * Get stored auth token
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored user data
 */
export function getStoredUser() {
  const userJson = localStorage.getItem(USER_KEY);
  if (userJson) {
    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Store auth data
 */
function storeAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Clear auth data
 */
export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Make authenticated API request
 */
async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}

/**
 * Register a new user
 */
export async function register(email, username, password) {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Registration failed");
  }

  const data = await response.json();
  storeAuth(data.access_token, data.user);
  return data.user;
}

/**
 * Login with email and password
 */
export async function login(email, password) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Login failed");
  }

  const data = await response.json();
  storeAuth(data.access_token, data.user);
  return data.user;
}

/**
 * Logout current user
 */
export async function logout() {
  const token = getToken();

  if (token) {
    try {
      await authFetch("/api/auth/logout", { method: "POST" });
    } catch (e) {
      // Ignore logout API errors
    }
  }

  clearAuth();
}

/**
 * Get current user profile (validates token)
 */
export async function getCurrentUser() {
  const token = getToken();
  if (!token) return null;

  const response = await authFetch("/api/auth/me");

  if (!response.ok) {
    clearAuth();
    return null;
  }

  const user = await response.json();
  // Update stored user data
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  return user;
}

/**
 * Check if user is logged in (quick check, no API call)
 */
export function isLoggedIn() {
  return !!getToken();
}
