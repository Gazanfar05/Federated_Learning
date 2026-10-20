export const HOSPITAL_ID = "hospital_03";
export const HOSPITAL_NAME = "Hospital 03 — Integrity & Audit Unit";
export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const API_URL_STORAGE_KEY = "hospital03.apiBaseUrl";

export function getApiBaseUrl() {
  try {
    return localStorage.getItem(API_URL_STORAGE_KEY) || DEFAULT_API_BASE_URL;
  } catch {
    return DEFAULT_API_BASE_URL;
  }
}

export function saveApiBaseUrl(value) {
  const parsed = new URL(value);
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("Use an http:// or https:// API URL.");
  }
  if (parsed.username || parsed.password) {
    throw new Error("Credentials must not be included in the API URL.");
  }
  const normalized = parsed.toString().replace(/\/+$/, "");
  localStorage.setItem(API_URL_STORAGE_KEY, normalized);
  return normalized;
}
