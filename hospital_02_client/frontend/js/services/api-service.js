import { hospitalConfig } from "../config/hospital-config.js";

function withTimeout(promise, timeoutMs) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("Request timed out")), timeoutMs);
    promise
      .then((value) => {
        clearTimeout(timer);
        resolve(value);
      })
      .catch((error) => {
        clearTimeout(timer);
        reject(error);
      });
  });
}

async function getJson(url, timeoutMs) {
  const response = await withTimeout(fetch(url, { method: "GET" }), timeoutMs);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

export class Hospital02ApiService {
  constructor(settings) {
    this.settings = settings;
  }

  updateSettings(settings) {
    this.settings = settings;
  }

  centralUrl(path) {
    return `${this.settings.centralApiBaseUrl}${path}`;
  }

  localUrl(path) {
    if (!this.settings.localAgentApiBaseUrl) {
      return "";
    }
    return `${this.settings.localAgentApiBaseUrl}${path}`;
  }

  async getHealth() {
    return getJson(this.centralUrl("/health"), this.settings.requestTimeoutMs);
  }

  async getTrainingStatus() {
    return getJson(this.centralUrl("/training/status"), this.settings.requestTimeoutMs);
  }

  async getModelCurrent() {
    return getJson(
      this.centralUrl(`/training/model?client_id=${encodeURIComponent(hospitalConfig.hospitalId)}`),
      this.settings.requestTimeoutMs
    );
  }

  async getMonitoringClients() {
    return getJson(this.centralUrl("/monitoring/clients"), this.settings.requestTimeoutMs);
  }

  async getDatasetValidationReport() {
    const url = this.localUrl("/dataset/validation/latest");
    if (!url) {
      throw new Error("Local validation agent URL is not configured");
    }
    return getJson(url, this.settings.requestTimeoutMs);
  }

  async getDatasetValidationHistory() {
    const url = this.localUrl("/dataset/validation/history");
    if (!url) {
      throw new Error("Local validation agent URL is not configured");
    }
    return getJson(url, this.settings.requestTimeoutMs);
  }

  async getFeatureQualityReport() {
    const url = this.localUrl("/dataset/features/quality/latest");
    if (!url) {
      throw new Error("Local validation agent URL is not configured");
    }
    return getJson(url, this.settings.requestTimeoutMs);
  }

  async getEvaluationLatest() {
    const url = this.localUrl("/evaluation/latest");
    if (!url) {
      throw new Error("Local validation agent URL is not configured");
    }
    return getJson(url, this.settings.requestTimeoutMs);
  }

  async getEvaluationHistory() {
    const url = this.localUrl("/evaluation/history");
    if (!url) {
      throw new Error("Local validation agent URL is not configured");
    }
    return getJson(url, this.settings.requestTimeoutMs);
  }

  async getModelComparison(leftVersion, rightVersion) {
    const url = this.localUrl(
      `/evaluation/comparison?left_version=${encodeURIComponent(leftVersion)}&right_version=${encodeURIComponent(rightVersion)}`
    );
    if (!this.settings.localAgentApiBaseUrl) {
      throw new Error("Local validation agent URL is not configured");
    }
    return getJson(url, this.settings.requestTimeoutMs);
  }

  async getTimelineEvents() {
    const url = this.localUrl("/timeline/events");
    if (!url) {
      throw new Error("Local validation agent URL is not configured");
    }
    return getJson(url, this.settings.requestTimeoutMs);
  }
}
