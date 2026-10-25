// Strip any trailing slash so paths never produce a double slash (which
// triggers a redirect that browsers refuse to follow on CORS preflight).
const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8009").replace(/\/+$/, "");

const ACCESS_KEY = "papermind_access";
const REFRESH_KEY = "papermind_refresh";

export function getAccess() {
  return localStorage.getItem(ACCESS_KEY);
}

export function setTokens(access, refresh) {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isAuthenticated() {
  return Boolean(getAccess());
}

// One refresh at a time: when several requests hit an expired token together
// they all wait for the same new access token instead of each asking for one.
let refreshing = null;

async function refreshAccess() {
  if (!refreshing) {
    refreshing = (async () => {
      const refresh = localStorage.getItem(REFRESH_KEY);
      if (!refresh) return false;
      try {
        const res = await fetch(API_URL + "/api/auth/token/refresh/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        setTokens(data.access, null);
        return true;
      } catch {
        return false;
      }
    })().finally(() => {
      refreshing = null;
    });
  }
  return refreshing;
}

/** The session is over: forget the tokens and go to sign in, remembering where we were. */
function sessionExpired() {
  clearTokens();
  if (window.location.pathname === "/login") return;
  const here = window.location.pathname + window.location.search;
  window.location.assign("/login?next=" + encodeURIComponent(here));
}

async function parse(res) {
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const message =
      (data && (data.detail || data.non_field_errors?.[0])) ||
      "Request failed (" + res.status + ")";
    const error = new Error(message);
    error.status = res.status;
    error.data = data;
    throw error;
  }
  return data;
}

export async function apiRequest(path, { method = "GET", body, form, retry = true } = {}) {
  const headers = {};
  const access = getAccess();
  if (access) headers["Authorization"] = "Bearer " + access;

  let payload;
  if (form) {
    payload = form;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(API_URL + path, { method, headers, body: payload });

  if (res.status === 401 && access) {
    if (retry && (await refreshAccess())) {
      return apiRequest(path, { method, body, form, retry: false });
    }
    sessionExpired();
    throw Object.assign(new Error("Your session has expired. Please sign in again."), { status: 401 });
  }
  return parse(res);
}

export const api = {
  register: (payload) => apiRequest("/api/auth/register/", { method: "POST", body: payload }),
  login: async (email, password) => {
    const data = await apiRequest("/api/auth/token/", {
      method: "POST",
      body: { email, password },
      retry: false,
    });
    setTokens(data.access, data.refresh);
    return data;
  },
  me: () => apiRequest("/api/auth/me/"),
  changePassword: (payload) => apiRequest("/api/auth/password/", { method: "POST", body: payload }),
  /** Exchange a Google ID token (from the Google button) for our JWT pair; creates the account on first use. */
  loginWithGoogle: async (credential) => {
    const data = await apiRequest("/api/auth/google/", { method: "POST", body: { credential }, retry: false });
    setTokens(data.access, data.refresh);
    return data;
  },

  listDocuments: () => apiRequest("/api/documents/"),
  uploadDocument: (file, title) => {
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    return apiRequest("/api/documents/", { method: "POST", form });
  },
  deleteDocument: (id) => apiRequest("/api/documents/" + id + "/", { method: "DELETE" }),

  createConversation: (documentId) =>
    apiRequest("/api/conversations/", { method: "POST", body: { document: documentId } }),
  listConversations: () => apiRequest("/api/conversations/"),
  getConversation: (id) => apiRequest("/api/conversations/" + id + "/"),
  deleteConversation: (id) => apiRequest("/api/conversations/" + id + "/", { method: "DELETE" }),
  ask: (conversationId, question) =>
    apiRequest("/api/conversations/" + conversationId + "/ask/", {
      method: "POST",
      body: { question },
    }),
};
