export function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

export function append(parent, ...children) {
  for (const child of children) {
    if (child) parent.append(child);
  }
  return parent;
}

export function sectionHeading(eyebrow, title, description, action) {
  const heading = element("div", "section-heading");
  const copy = element("div", "section-heading-copy");
  append(
    copy,
    element("div", "eyebrow", eyebrow),
    element("h1", "", title),
    element("p", "page-description", description),
  );
  append(heading, copy, action);
  return heading;
}

export function panel(title, subtitle) {
  const wrapper = element("section", "panel");
  const header = element("div", "panel-header");
  const body = element("div", "panel-body");
  append(header, element("h2", "panel-title", title));
  if (subtitle) append(header, element("p", "panel-subtitle", subtitle));
  append(wrapper, header, body);
  return { wrapper, header, body };
}

export function definitionList(items, options = {}) {
  const list = element("dl", `definition-list${options.compact ? " compact" : ""}`);
  for (const [label, value, className] of items) {
    const row = element("div", "definition-row");
    append(row, element("dt", "", label), element("dd", className || "", value));
    list.append(row);
  }
  return list;
}

export function statePill(label, variant = "neutral") {
  const pill = element("span", `state-pill ${variant}`);
  append(pill, element("span", "pill-dot"), element("span", "", label));
  return pill;
}

export function metadataValue(value, className = "") {
  if (value === undefined || value === null || value === "") {
    return element("span", "muted", "Unavailable");
  }
  return element("span", className, String(value));
}

export function renderModelManifest(metadata) {
  const manifest = panel("Model manifest", "Metadata reported by the coordinator; this is not an artifact manifest.");
  const rows = [
    ["Model version", metadata?.model_version === undefined ? null : `v${metadata.model_version}`],
    ["Round number", metadata?.round_id],
    ["Architecture", metadata?.architecture],
    ["Parameter count", metadata?.parameter_count?.toLocaleString?.()],
    ["Artifact availability", "No artifact retrieval endpoint"],
    ["Reported digest field", metadata?.update_hash],
    ["Locally computed digest", "Not available — artifact bytes were not retrieved"],
  ];
  manifest.body.append(definitionList(rows.map(([name, value]) => [
    name,
    value === null || value === undefined ? "Unavailable" : String(value),
    name === "Reported digest field" ? "mono digest-value" : "",
  ])));

  const note = element("div", "notice notice-amber");
  append(
    note,
    element("span", "notice-mark", "!"),
    element("p", "", "Verification not performed. The coordinator's digest field is metadata only; no model bytes or trusted expected digest are available to compare."),
  );
  manifest.body.append(note);
  return manifest.wrapper;
}

export function renderAuditTimeline(events = []) {
  const timeline = panel("Audit timeline", "Structured events are shown only when supplied by a trusted, documented event source.");
  if (events.length) {
    const list = element("ol", "timeline-list");
    for (const event of events) list.append(renderAuditEvent(event));
    timeline.body.append(list);
  } else {
    const empty = element("div", "empty-state");
    const icon = element("div", "empty-mark", "—");
    icon.setAttribute("aria-hidden", "true");
    append(
      empty,
      icon,
      element("h3", "", "No audit events available"),
      element("p", "", "The current API does not expose structured audit or OpenFL lifecycle events. No events are inferred from model metadata or coordinator health."),
    );
    timeline.body.append(empty);
  }

  const sources = element("div", "source-grid");
  sources.append(sourceCard("Application events", "Unavailable", "No audit-events endpoint is exposed.", "unavailable"));
  sources.append(sourceCard("OpenFL lifecycle", "Unavailable", "No configured lifecycle JSONL source is exposed to this portal.", "unavailable"));
  sources.append(sourceCard("Model transfer evidence", "Not provided", "A lifecycle record alone would not establish transfer or broadcast success.", "neutral"));
  timeline.body.append(sources);
  return timeline.wrapper;
}

function renderAuditEvent(event) {
  const item = element("li", "timeline-item");
  const marker = element("span", "timeline-marker");
  marker.setAttribute("aria-hidden", "true");
  const content = element("div", "timeline-event");
  const header = element("div", "timeline-event-header");
  const kind = event.source_type === "openfl_lifecycle"
    ? "OpenFL lifecycle"
    : event.source_type === "application"
      ? "Application-level"
      : "Event";
  append(header, element("strong", "timeline-event-type", event.event_type || "Unspecified event"), statePill(kind, "neutral"));

  const timestamp = element("time", "timeline-timestamp", formatEventTimestamp(event.timestamp));
  if (typeof event.timestamp === "string") timestamp.dateTime = event.timestamp;
  const message = element("p", "timeline-message", event.message || "No event message supplied.");
  const details = definitionList([
    ["Hospital identifier", event.hospital_id ?? "Not supplied", "mono"],
    ["Round number", event.round_number ?? "Not supplied", "mono"],
    ["Operation identifier", event.operation_id ?? "Not supplied", "mono"],
    ["Source / provenance", event.source ?? event.provenance ?? "Not supplied"],
  ]);
  append(content, header, timestamp, message, details);
  append(item, marker, content);
  return item;
}

function formatEventTimestamp(value) {
  if (!value) return "Timestamp not supplied";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : formatTimestamp(date);
}

function sourceCard(title, state, description, variant) {
  const card = element("div", "source-card");
  append(
    card,
    element("div", "source-card-top", title),
    statePill(state, variant),
    element("p", "", description),
  );
  return card;
}

export function renderConnectionStatus(snapshot) {
  const { data, error, updatedAt, loading } = snapshot;
  if (loading && !data) return statePill("Checking", "pending");
  if (error && !data) return statePill("Unavailable", "danger");
  if (error && data) return statePill("Stale", "warning");
  if (data) return statePill("Reachable", "success");
  return statePill("Not checked", "neutral");
}

export function formatTimestamp(value) {
  if (!value) return "Never";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(value);
}
