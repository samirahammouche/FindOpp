// One place for URLs, tokens and error handling.
const TOKEN_KEY = "access";
const USER_KEY = "user";

export const session = {
  token: () => localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY),
  user() {
    const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    try { return raw ? JSON.parse(raw) : null; } catch { return null; }
  },
  // "Keep me signed in" -> localStorage (survives closing the browser)
  save(token, user, remember) {
    this.clear();
    const store = remember ? localStorage : sessionStorage;
    store.setItem(TOKEN_KEY, token);
    store.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    [localStorage, sessionStorage].forEach((s) => {
      s.removeItem(TOKEN_KEY);
      s.removeItem(USER_KEY);
    });
  },
};

// Turns Django/DRF error bodies into one readable sentence.
function errorMessage(data, fallback) {
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  if (data.message || data.error) return data.message || data.error;

  const [field, msgs] = Object.entries(data)[0] || [];
  if (!field) return fallback;
  const text = Array.isArray(msgs) ? msgs[0] : String(msgs);
  if (field === "non_field_errors") return text;
  const label = field.replace(/_/g, " ");
  return `${label.charAt(0).toUpperCase() + label.slice(1)}: ${text}`;
}

export async function api(path, { body, headers = {}, ...options } = {}) {
  const h = { ...headers };

  // Never send a (possibly expired) token to the public auth endpoints
  const isPublicAuth = /^\/api\/auth\/(login|register|refresh)\/?$/.test(path);
  const token = session.token();
  if (token && !isPublicAuth) h.Authorization = `Bearer ${token}`;

  let payload = body;
  if (body && !(body instanceof FormData)) {
    h["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  } // FormData: the browser sets the multipart boundary itself

  const res = await fetch(path, { ...options, headers: h, body: payload });
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const err = new Error(errorMessage(data, "Something went wrong. Try again."));
    err.status = res.status;
    throw err;
  }
  return data;
}