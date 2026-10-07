// Local state of the web test build, kept in this browser's localStorage (the Android app uses the Keystore-backed
// flutter_secure_storage instead). Photos and heat maps are never stored: saved results are text only.
// If storage is blocked (private mode, strict settings) everything still works for the current tab, in memory.

const PREFIX = "glowrithm.";
const memory = new Map();
export const MAX_HISTORY = 50;
export const CONSENT_VERSION = "2026-10-web";

function read(key, fallback) {
  try {
    const raw = window.localStorage.getItem(PREFIX + key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch {
    return memory.has(key) ? memory.get(key) : fallback;
  }
}

function write(key, value) {
  memory.set(key, value);
  try {
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    /* storage unavailable: the in-memory copy is used for this tab */
  }
}

function remove(key) {
  memory.delete(key);
  try {
    window.localStorage.removeItem(PREFIX + key);
  } catch {
    /* nothing stored */
  }
}

export const getConsent = () => read("consent", null);
export const grantConsent = () => write("consent", { version: CONSENT_VERSION, granted_at: new Date().toISOString() });

export const getProfile = () => read("profile", null);
export const saveProfile = (profile) => write("profile", profile);

export const getHistory = () => read("history", []);
export const isSaved = (requestId) => getHistory().some((entry) => entry.request_id === requestId);
export const findSaved = (requestId) => getHistory().find((entry) => entry.request_id === requestId) || null;

/** Saves a result without its face photo and heat map; keeps the newest MAX_HISTORY entries. */
export function saveResult(result) {
  const entry = { ...result, face_image: null, heatmap_image: null, saved_at: new Date().toISOString() };
  const rest = getHistory().filter((item) => item.request_id !== result.request_id);
  write("history", [entry, ...rest].slice(0, MAX_HISTORY));
}

export const deleteResult = (requestId) =>
  write("history", getHistory().filter((item) => item.request_id !== requestId));
export const clearHistory = () => write("history", []);

export const getSettings = () => ({ serverUrl: "", apiKey: "", ...read("settings", {}) });
export const saveSettings = (settings) => write("settings", settings);

/** Withdraw consent: erase everything this app stored in the browser. */
export function eraseAll() {
  ["consent", "profile", "history", "settings"].forEach(remove);
}
