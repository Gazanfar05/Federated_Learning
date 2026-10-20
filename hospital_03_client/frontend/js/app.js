import { DEFAULT_API_BASE_URL, HOSPITAL_ID, HOSPITAL_NAME, getApiBaseUrl, saveApiBaseUrl } from "./config.js";
import { fetchHealth, fetchModelMetadata } from "./api.js";
import {
  append,
  definitionList,
  element,
  formatTimestamp,
  metadataValue,
  panel,
  renderAuditTimeline,
  renderConnectionStatus,
  renderModelManifest,
  sectionHeading,
  statePill,
} from "./components.js";

const pages = {
  overview: { label: "SECURITY OVERVIEW", title: "Security overview" },
  integrity: { label: "MODEL INTEGRITY", title: "Model integrity" },
  identity: { label: "IDENTITY & CONNECTIVITY", title: "Identity & connectivity" },
  updates: { label: "UPDATE REVIEW", title: "Update integrity review" },
  audit: { label: "AUDIT TIMELINE", title: "Audit timeline" },
  warnings: { label: "INTEGRITY WARNINGS", title: "Integrity warnings" },
};

const state = {
  page: "overview",
  health: { loading: false, data: null, error: null, updatedAt: null },
  model: { loading: false, data: null, error: null, updatedAt: null },
  notice: "",
};

const pageContent = document.querySelector("#page-content");
const apiIndicator = document.querySelector("#api-indicator");
const apiIndicatorLabel = document.querySelector("#api-indicator-label");
const announcer = document.querySelector("#announcer");

document.querySelector("#refresh-button").addEventListener("click", refreshData);
document.querySelector(".nav-list").addEventListener("click", (event) => {
  const link = event.target.closest("[data-page]");
  if (!link) return;
  event.preventDefault();
  navigate(link.dataset.page);
});
pageContent.addEventListener("submit", (event) => {
  if (event.target.id !== "api-config-form") return;
  event.preventDefault();
  saveApiConfiguration(new FormData(event.target).get("api-url"));
});
pageContent.addEventListener("click", (event) => {
  if (event.target.closest("[data-action='refresh']")) refreshData();
});
window.addEventListener("hashchange", () => navigate(location.hash.slice(1), false));

function navigate(page, updateHash = true) {
  const nextPage = pages[page] ? page : "overview";
  state.page = nextPage;
  if (updateHash && location.hash !== `#${nextPage}`) location.hash = nextPage;
  document.querySelectorAll(".nav-link").forEach((link) => {
    const active = link.dataset.page === nextPage;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  document.querySelector("#current-section").textContent = pages[nextPage].label;
  render();
}

function render() {
  pageContent.replaceChildren();
  if (state.page === "overview") renderOverview();
  if (state.page === "integrity") renderIntegrity();
  if (state.page === "identity") renderIdentity();
  if (state.page === "updates") renderUpdates();
  if (state.page === "audit") renderAudit();
  if (state.page === "warnings") renderWarnings();
  updateApiIndicator();
  if (state.notice) {
    announcer.textContent = state.notice;
    state.notice = "";
  }
}

function renderOverview() {
  const headingAction = makeRefreshButton();
  pageContent.append(sectionHeading(
    "HOSPITAL 03 · SECURITY OPERATIONS",
    "Security overview",
    "A read-only view of coordinator connectivity and model metadata. Authentication, OpenFL runtime state, and artifact integrity are not inferred.",
    headingAction,
  ));

  const summary = element("div", "summary-grid");
  summary.append(summaryCard("Central API", renderConnectionStatus(state.health), healthDetail()));
  summary.append(summaryCard("Application session", statePill("Not exposed", "neutral"), "No session-status API is available."));
  summary.append(summaryCard("OpenFL collaborator", statePill("No evidence", "neutral"), "No genuine OpenFL runtime status is exposed."));
  summary.append(summaryCard("Artifact verification", statePill("Not verified", "warning"), "No artifact bytes or trusted digest are available."));
  pageContent.append(summary);

  const layout = element("div", "content-grid overview-grid");
  const modelPanel = panel("Current model metadata", "Coordinator response — informational only.");
  const data = state.model.data;
  modelPanel.body.append(definitionList([
    ["Model version", data?.model_version === undefined ? "Unavailable" : `v${data.model_version}`],
    ["Round number", data?.round_id ?? "Unavailable"],
    ["Architecture", data?.architecture ?? "Unavailable"],
    ["Reported digest", data?.update_hash ?? "Unavailable", "mono digest-value"],
  ]));
  if (state.model.error) modelPanel.body.append(errorBox(state.model.error, state.model.updatedAt));
  append(modelPanel.body, metadataLink("View complete manifest", "integrity"));
  layout.append(modelPanel.wrapper);

  const warningsPanel = panel("Current checks", "Observed state only; unsupported checks remain unavailable.");
  warningsPanel.body.append(checkList([
    ["Central API health", checkState(state.health), healthDetail()],
    ["Model metadata", checkState(state.model), modelDetail()],
    ["Session status", "Unavailable", "No session endpoint."],
    ["Audit event source", "Unavailable", "No structured event endpoint."],
  ]));
  layout.append(warningsPanel.wrapper);
  pageContent.append(layout);

  const timelinePanel = panel("Most recent audit events", "Only sourced events can appear here.");
  const eventEmpty = element("div", "compact-empty");
  append(eventEmpty, element("span", "compact-empty-mark", "—"), element("p", "", "No event source is currently available."));
  timelinePanel.body.append(eventEmpty);
  append(timelinePanel.body, metadataLink("Open audit timeline", "audit"));
  pageContent.append(timelinePanel.wrapper);
}

function renderIntegrity() {
  pageContent.append(sectionHeading(
    "MODEL PROVENANCE",
    "Model integrity",
    "Inspect what the coordinator reports without treating metadata as cryptographic verification.",
  ));
  pageContent.append(renderModelManifest(state.model.data));
  if (state.model.error) pageContent.append(errorBox(state.model.error, state.model.updatedAt));

  const notes = panel("Verification requirements", "A verified state requires all of the following.");
  notes.body.append(checkList([
    ["Artifact retrieval", "Unavailable", "No route currently provides the model artifact bytes."],
    ["Trusted expected digest", "Unavailable", "No signed or otherwise trusted manifest is exposed."],
    ["Independent digest calculation", "Not performed", "No bytes are available for local hashing."],
    ["Digest comparison", "Not performed", "There are no two trusted values to compare."],
  ]));
  pageContent.append(notes.wrapper);
}

function renderIdentity() {
  pageContent.append(sectionHeading(
    "CONFIGURATION & HEALTH",
    "Identity & connectivity",
    "The hospital identifier is fixed in this frontend. It is configuration, not authentication or proof of certificate validation.",
    makeRefreshButton(),
  ));

  const grid = element("div", "content-grid");
  const identityPanel = panel("Configured identity", "No credentials or private key material are stored in the browser.");
  identityPanel.body.append(definitionList([
    ["Hospital identifier", HOSPITAL_ID, "mono"],
    ["Display name", HOSPITAL_NAME],
    ["Browser session", "Not exposed by backend"],
    ["Certificate status", "Not exposed by backend"],
    ["Client certificate validation", "Not asserted by this portal"],
  ]));
  grid.append(identityPanel.wrapper);

  const healthPanel = panel("Central API health", "GET /health — read-only coordinator health check.");
  const healthContent = element("div", "connection-summary");
  append(
    healthContent,
    renderConnectionStatus(state.health),
    definitionList([
      ["Configured API URL", getApiBaseUrl(), "mono break-word"],
      ["Last successful check", formatTimestamp(state.health.updatedAt)],
      ["Observed status", state.health.data?.status ?? "Unavailable"],
      ["Reported service", state.health.data?.service ?? "Unavailable"],
      ["Last health failure", state.health.error ?? "None observed"],
    ]),
  );
  if (state.health.error) healthContent.append(errorBox(state.health.error, state.health.updatedAt));
  healthPanel.body.append(healthContent);
  grid.append(healthPanel.wrapper);
  pageContent.append(grid);

  const configPanel = panel("API endpoint", "Stored in this browser only. Do not include credentials or secrets in the URL.");
  const form = element("form", "api-config-form");
  form.id = "api-config-form";
  const label = element("label", "field-label", "Central API base URL");
  label.htmlFor = "api-url";
  const input = element("input", "text-input");
  input.id = "api-url";
  input.name = "api-url";
  input.type = "url";
  input.required = true;
  input.autocomplete = "url";
  input.value = getApiBaseUrl();
  input.placeholder = DEFAULT_API_BASE_URL;
  const help = element("p", "field-help", "Example: http://127.0.0.1:8000. Browser requests do not include credentials.");
  const save = element("button", "button button-primary", "Save endpoint");
  save.type = "submit";
  append(form, label, input, help, element("div", "form-actions"));
  form.querySelector(".form-actions").append(save);
  configPanel.body.append(form);
  pageContent.append(configPanel.wrapper);
}

function renderUpdates() {
  pageContent.append(sectionHeading(
    "READ-ONLY REVIEW",
    "Update integrity review",
    "This page is prepared for future update records. It does not submit, accept, or reject model updates.",
  ));

  const updatePanel = panel("Update artifact record", "No update-review endpoint or persisted review record is available.");
  updatePanel.body.append(definitionList([
    ["Update identifier", "Unavailable"],
    ["Base-model version", "Unavailable"],
    ["Round identifier", "Unavailable"],
    ["Artifact digest", "Unavailable"],
    ["Digest-verification status", "Unavailable"],
    ["Validation state", "Unavailable"],
    ["Server receipt identifier", "Unavailable"],
    ["Acceptance / rejection reason", "Unavailable"],
  ]));
  const note = element("div", "notice notice-slate");
  append(note, element("span", "notice-mark", "i"), element("p", "", "The demonstration coordinator's POST /training/update route is not used here and is not represented as genuine OpenFL transport or update submission."));
  updatePanel.body.append(note);
  pageContent.append(updatePanel.wrapper);
}

function renderAudit() {
  pageContent.append(sectionHeading(
    "EVENT PROVENANCE",
    "Audit timeline",
    "Application and OpenFL lifecycle events are distinct sources. No event is fabricated from a health check or model response.",
  ));
  pageContent.append(renderAuditTimeline());
}

function renderWarnings() {
  pageContent.append(sectionHeading(
    "OBSERVED VS. UNAVAILABLE",
    "Integrity warnings",
    "An incident is reported only when returned data supports it. Future checks are documented separately.",
  ));
  const observed = panel("Observed incidents", "Warnings supported by current endpoint responses.");
  const incidentState = state.health.error || state.model.error
    ? (state.health.error ? state.health : state.model)
    : null;
  if (incidentState) {
    observed.body.append(errorBox(incidentState.error, incidentState.updatedAt));
  } else {
    const none = element("div", "empty-state compact");
    append(none, element("h3", "", "No observed incidents"), element("p", "", "This does not imply that artifact integrity, authentication, or OpenFL operation has been verified."));
    observed.body.append(none);
  }
  pageContent.append(observed.wrapper);

  const documented = panel("Checks requiring future evidence", "These are capabilities or unavailable checks, not current incidents.");
  documented.body.append(checkList([
    ["Missing model artifact", "Unavailable check", "No artifact retrieval contract."],
    ["Digest mismatch", "Unavailable check", "No trusted expected digest or artifact bytes."],
    ["Stale model version", "Unavailable check", "No freshness policy or trusted version reference."],
    ["Invalid manifest", "Unavailable check", "No signed manifest is exposed."],
    ["Unavailable audit source", "Unavailable", "No event endpoint is exposed."],
    ["Rejected update", "Unavailable check", "No read-only update-review endpoint is exposed."],
  ]));
  pageContent.append(documented.wrapper);
}

function summaryCard(title, status, detail) {
  const card = element("section", "summary-card");
  append(card, element("div", "summary-label", title), status, element("p", "summary-detail", detail));
  return card;
}

function checkList(rows) {
  const list = element("div", "check-list");
  for (const [title, status, detail] of rows) {
    const row = element("div", "check-row");
    const copy = element("div", "check-copy");
    append(copy, element("strong", "", title), element("span", "", detail));
    append(row, copy, statePill(status, variantForStatus(status)));
    list.append(row);
  }
  return list;
}

function errorBox(message, lastSuccess) {
  const box = element("div", "error-box");
  const title = lastSuccess ? "Connection issue — showing last successful response" : "Data unavailable";
  append(box, element("strong", "", title), element("p", "", message));
  if (lastSuccess) append(box, element("span", "stale-label", `Last successful response: ${formatTimestamp(lastSuccess)}`));
  return box;
}

function makeRefreshButton() {
  const button = element("button", "button button-quiet", "Refresh data");
  button.type = "button";
  button.dataset.action = "refresh";
  button.disabled = state.health.loading || state.model.loading;
  return button;
}

function metadataLink(label, page) {
  const link = element("a", "text-link", label);
  link.href = `#${page}`;
  link.addEventListener("click", (event) => {
    event.preventDefault();
    navigate(page);
  });
  return link;
}

function healthDetail() {
  if (state.health.error) return state.health.updatedAt
    ? `Stale response · last success ${formatTimestamp(state.health.updatedAt)}`
    : state.health.error;
  if (state.health.data) return `Last checked ${formatTimestamp(state.health.updatedAt)}`;
  return state.health.loading ? "Read-only health check in progress." : "Waiting for a health check.";
}

function modelDetail() {
  if (state.model.error) return state.model.updatedAt
    ? `Stale metadata · last success ${formatTimestamp(state.model.updatedAt)}`
    : state.model.error;
  return state.model.data ? "Metadata response received; artifact not verified." : "Waiting for model metadata.";
}

function checkState(snapshot) {
  if (snapshot.error) return snapshot.updatedAt ? "Stale" : "Unavailable";
  if (snapshot.data) return "Available";
  if (snapshot.loading) return "Checking";
  return "Not checked";
}

function variantForStatus(status) {
  if (["Available", "Reachable"].includes(status)) return "success";
  if (["Stale", "Unavailable check"].includes(status)) return "warning";
  if (["Unavailable", "No evidence", "Not exposed", "Not verified", "Not performed"].includes(status)) return "neutral";
  return "neutral";
}

function updateApiIndicator() {
  const current = state.health;
  const status = current.error ? (current.data ? "stale" : "unavailable") : current.data ? "reachable" : "unknown";
  apiIndicator.dataset.state = status;
  apiIndicatorLabel.textContent = {
    stale: "API DATA STALE",
    unavailable: "API UNAVAILABLE",
    reachable: "API REACHABLE",
    unknown: "API STATUS UNKNOWN",
  }[status];
}

async function refreshData() {
  if (state.health.loading || state.model.loading) return;
  state.health.loading = true;
  state.model.loading = true;
  state.health.error = null;
  state.model.error = null;
  state.notice = "Refreshing read-only coordinator health and model metadata.";
  render();

  const results = await Promise.allSettled([fetchHealth(), fetchModelMetadata()]);
  const timestamp = new Date();
  [state.health, state.model].forEach((snapshot, index) => {
    snapshot.loading = false;
    const result = results[index];
    if (result.status === "fulfilled") {
      snapshot.data = result.value;
      snapshot.error = null;
      snapshot.updatedAt = timestamp;
    } else {
      snapshot.error = result.reason instanceof Error ? result.reason.message : "Request failed.";
    }
  });
  state.notice = "Refresh complete.";
  render();
}

function saveApiConfiguration(value) {
  try {
    saveApiBaseUrl(String(value || "").trim());
    state.notice = "API endpoint saved. Refreshing read-only data.";
    state.health.data = null;
    state.health.updatedAt = null;
    state.model.data = null;
    state.model.updatedAt = null;
    render();
    refreshData();
  } catch (error) {
    state.notice = error instanceof Error ? error.message : "The API endpoint could not be saved.";
    render();
    const message = element("p", "form-error", state.notice);
    pageContent.querySelector("#api-config-form")?.append(message);
  }
}

navigate(location.hash.slice(1) || "overview", false);
refreshData();
