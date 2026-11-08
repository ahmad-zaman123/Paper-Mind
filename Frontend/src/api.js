// The API is served from this site's own address: Vercel forwards /api to the backend, and so does the Vite dev
// server. That keeps the session cookies first-party.
const API_URL = "";

// The session lives in httpOnly cookies that this script can't read. This flag only remembers that someone signed
// in, so the app can pick the right page before asking the server. It is not a credential.
const SIGNED_IN = "papermind_signed_in";

// Tokens used to be kept here. Drop any left over from before.
try {
  localStorage.removeItem("papermind_access");
  localStorage.removeItem("papermind_refresh");
} catch {
  /* storage blocked */
}

function markSignedIn() {
  try {
    localStorage.setItem(SIGNED_IN, "1");
  } catch {
    /* storage blocked: the app still works, it just starts on the landing page */
  }
}

/** Forget the session in this browser: the server clears the cookies, and the local flag goes too. */
export function clearSession() {
  try {
    localStorage.removeItem(SIGNED_IN);
  } catch {
    /* storage blocked */
  }
  return fetch(API_URL + "/api/auth/logout/", { method: "POST" }).catch(() => {});
}

export function isAuthenticated() {
  try {
    return localStorage.getItem(SIGNED_IN) === "1";
  } catch {
    return false;
  }
}

// One refresh at a time: when several requests hit an expired token together
// they all wait for the same new access token instead of each asking for one.
let refreshing = null;

async function refreshAccess() {
  if (!refreshing) {
    refreshing = fetch(API_URL + "/api/auth/token/refresh/", { method: "POST" })
      .then((res) => res.ok)
      .catch(() => false)
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

/** The session is over: forget the tokens and go to sign in, remembering where we were. */
function sessionExpired() {
  clearSession();
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

  let payload;
  if (form) {
    payload = form;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(API_URL + path, { method, headers, body: payload });

  if (res.status === 401 && isAuthenticated()) {
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
    markSignedIn();
    return data;
  },
  logout: () => clearSession(),
  me: () => apiRequest("/api/auth/me/"),
  /** Changing the password ends every session. The server sets new cookies for this one. */
  changePassword: (payload) => apiRequest("/api/auth/password/", { method: "POST", body: payload }),
  forgotPassword: (email) => apiRequest("/api/auth/password/forgot/", { method: "POST", body: { email }, retry: false }),
  resetPassword: (payload) => apiRequest("/api/auth/password/reset/", { method: "POST", body: payload, retry: false }),
  /** Exchange a Google ID token (from the Google button) for our JWT pair; creates the account on first use. */
  /** A private demo: the server makes a fresh account with a copy of the sample document and signs us in. */
  startDemo: async () => {
    const data = await apiRequest("/api/auth/demo/", { method: "POST", retry: false });
    markSignedIn();
    return data;
  },
  loginWithGoogle: async (credential) => {
    const data = await apiRequest("/api/auth/google/", { method: "POST", body: { credential }, retry: false });
    markSignedIn();
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
