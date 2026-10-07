// Client for the Glowrithm REST API (backend/app/main.py). Mirrors mobile/lib/services/api_service.dart.
import { getSettings } from "./store.js";

export class ApiError extends Error {
  /** retake = the photo was rejected (quality gate or no face): a new photo is needed, not a retry. */
  constructor(message, { status = null, retake = false } = {}) {
    super(message);
    this.status = status;
    this.retake = retake;
  }
}

/** API root: the address saved in Profile > Server settings, or the server that served this page. */
export function baseUrl(override) {
  const configured = String(override ?? getSettings().serverUrl ?? "").trim().replace(/\/+$/, "");
  if (configured) return configured;
  return window.location.protocol.startsWith("http") ? window.location.origin : null;
}

export function isValidAddress(value) {
  try {
    const url = new URL(value);
    return (url.protocol === "http:" || url.protocol === "https:") && Boolean(url.hostname);
  } catch {
    return false;
  }
}

async function call(path, init = {}, { timeoutMs = 60000, base } = {}) {
  const root = baseUrl(base);
  if (!root) throw new ApiError("Set the API address in Profile > Server settings.");
  const headers = new Headers(init.headers || {});
  const apiKey = getSettings().apiKey;
  if (apiKey) headers.set("X-API-Key", apiKey);
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  let response;
  try {
    response = await fetch(root + path, { ...init, headers, signal: controller.signal, cache: "no-store" });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new ApiError("The server took too long to respond. Check your connection and try again.");
    }
    throw new ApiError(`Cannot reach the server at ${root}. Check the address in Profile > Server settings.`);
  } finally {
    window.clearTimeout(timer);
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok && body && typeof body === "object") return body;
  const detail = body && body.detail;
  if (typeof detail === "string") {
    // 422 with a text detail comes from the photo-quality gate or the face check; validation errors are lists.
    throw new ApiError(detail, { status: response.status, retake: response.status === 422 });
  }
  if (Array.isArray(detail) && detail.length) {
    const reasons = detail.map((item) => `${(item.loc || []).slice(-1)[0] ?? "field"}: ${item.msg}`).join("; ");
    throw new ApiError(`The server did not accept the request (${reasons}).`, { status: response.status });
  }
  throw new ApiError(`The server returned an error (HTTP ${response.status}).`, { status: response.status });
}

export const health = (base) => call("/api/v1/health", {}, { timeoutMs: 10000, base });

/** Uploads one photo with the profile and explicit consent; returns the full analysis. */
export function analyze({ blob, age, sex }) {
  const form = new FormData();
  form.append("image", blob, "photo.jpg");
  form.append("consent", "true");
  form.append("age", String(age));
  form.append("sex", sex);
  return call("/api/v1/analyze", { method: "POST", body: form }, { timeoutMs: 90000 });
}
