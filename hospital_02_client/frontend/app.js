import { hospitalConfig } from "./js/config/hospital-config.js";
import { Hospital02ApiService } from "./js/services/api-service.js";
import { PortalController } from "./js/components/portal-controller.js";

function loadSettings() {
  const raw = localStorage.getItem(hospitalConfig.storageKey);
  if (!raw) {
    return {
      centralApiBaseUrl: hospitalConfig.centralApiBaseUrl,
      localAgentApiBaseUrl: hospitalConfig.localAgentApiBaseUrl,
      requestTimeoutMs: hospitalConfig.requestTimeoutMs,
      staleDataMs: hospitalConfig.staleDataMs
    };
  }

  try {
    const parsed = JSON.parse(raw);
    return {
      centralApiBaseUrl: parsed.centralApiBaseUrl || hospitalConfig.centralApiBaseUrl,
      localAgentApiBaseUrl: parsed.localAgentApiBaseUrl || hospitalConfig.localAgentApiBaseUrl,
      requestTimeoutMs: Number(parsed.requestTimeoutMs) || hospitalConfig.requestTimeoutMs,
      staleDataMs: Number(parsed.staleDataMs) || hospitalConfig.staleDataMs
    };
  } catch {
    return {
      centralApiBaseUrl: hospitalConfig.centralApiBaseUrl,
      localAgentApiBaseUrl: hospitalConfig.localAgentApiBaseUrl,
      requestTimeoutMs: hospitalConfig.requestTimeoutMs,
      staleDataMs: hospitalConfig.staleDataMs
    };
  }
}

function saveSettings(settings) {
  localStorage.setItem(hospitalConfig.storageKey, JSON.stringify(settings));
}

function bindNavigation() {
  const nav = document.getElementById("sideNav");
  if (!nav) {
    return;
  }

  nav.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-page]");
    if (!button) {
      return;
    }

    const page = button.dataset.page;
    document.querySelectorAll(".nav-btn").forEach((node) => node.classList.remove("active"));
    button.classList.add("active");

    document.querySelectorAll(".page").forEach((section) => section.classList.remove("active"));
    const nextPage = document.getElementById(`page-${page}`);
    if (nextPage) {
      nextPage.classList.add("active");
    }
  });
}

function wireSettings(controller, settings) {
  const panel = document.getElementById("settingsPanel");
  const toggleBtn = document.getElementById("toggleSettingsBtn");
  const saveBtn = document.getElementById("saveSettingsBtn");

  const centralApiInput = document.getElementById("centralApiInput");
  const localAgentInput = document.getElementById("localAgentInput");
  const timeoutInput = document.getElementById("timeoutInput");
  const staleInput = document.getElementById("staleInput");

  centralApiInput.value = settings.centralApiBaseUrl;
  localAgentInput.value = settings.localAgentApiBaseUrl;
  timeoutInput.value = String(settings.requestTimeoutMs);
  staleInput.value = String(settings.staleDataMs);

  toggleBtn.addEventListener("click", () => {
    panel.classList.toggle("hidden");
  });

  saveBtn.addEventListener("click", () => {
    const nextSettings = {
      centralApiBaseUrl: centralApiInput.value.trim(),
      localAgentApiBaseUrl: localAgentInput.value.trim(),
      requestTimeoutMs: Number(timeoutInput.value) || hospitalConfig.requestTimeoutMs,
      staleDataMs: Number(staleInput.value) || hospitalConfig.staleDataMs
    };

    saveSettings(nextSettings);
    controller.updateSettings(nextSettings);
    controller.refreshAll();
  });
}

function bindRetryButtons(controller) {
  document.getElementById("refreshAllBtn")?.addEventListener("click", () => controller.refreshAll());
  document.getElementById("retryLatestEval")?.addEventListener("click", () => controller.refreshOverview());
  document.getElementById("retryValidationHistory")?.addEventListener("click", () => controller.refreshOverview());
  document.getElementById("retryValidationBtn")?.addEventListener("click", () => controller.refreshValidation());
  document.getElementById("retryFeatureBtn")?.addEventListener("click", () => controller.refreshFeatureQuality());
  document.getElementById("retryEvaluationBtn")?.addEventListener("click", () => controller.refreshEvaluation());
  document.getElementById("retryComparisonBtn")?.addEventListener("click", () => {
    const left = document.getElementById("leftModelInput")?.value.trim();
    const right = document.getElementById("rightModelInput")?.value.trim();
    controller.refreshComparison(left, right);
  });
  document.getElementById("retryHistoryBtn")?.addEventListener("click", () => controller.refreshHistory());

  document.getElementById("loadComparisonBtn")?.addEventListener("click", () => {
    const left = document.getElementById("leftModelInput")?.value.trim();
    const right = document.getElementById("rightModelInput")?.value.trim();
    controller.refreshComparison(left, right);
  });
}

async function init() {
  bindNavigation();

  const settings = loadSettings();
  const api = new Hospital02ApiService(settings);
  const controller = new PortalController(api, settings);

  wireSettings(controller, settings);
  bindRetryButtons(controller);

  await controller.refreshAll();

  setInterval(() => {
    controller.updateStaleBadge();
  }, 1000);
}

init();
