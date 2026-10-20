import { HOSPITAL_ID, getApiBaseUrl } from "./config.js";

const REQUEST_TIMEOUT_MS = 8000;

async function getJson(path) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      credentials: "omit",
      cache: "no-store",
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Request failed with HTTP ${response.status}.`);
    }

    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(`Request timed out after ${REQUEST_TIMEOUT_MS / 1000} seconds.`);
    }
    if (error instanceof TypeError) {
      throw new Error("The API could not be reached. Check the URL, server, and browser CORS settings.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export function fetchHealth() {
  return getJson("/health");
}

export function fetchModelMetadata() {
  const params = new URLSearchParams({ client_id: HOSPITAL_ID });
  return getJson(`/model/current?${params.toString()}`);
}
