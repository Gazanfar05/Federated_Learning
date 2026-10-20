export function setSafeText(element, value) {
  if (!element) {
    return;
  }
  element.textContent = value ?? "";
}

export function createElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (typeof text === "string") {
    node.textContent = text;
  }
  return node;
}

export function clearNode(element) {
  if (!element) {
    return;
  }
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

export function formatTimestamp(value) {
  if (!value) {
    return "Unavailable";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Unavailable";
  }
  return parsed.toLocaleString();
}

export function toBadgeClass(status) {
  const normalized = String(status || "").toLowerCase();
  if (["ok", "healthy", "available", "ready", "valid"].includes(normalized)) {
    return "badge badge-ok";
  }
  if (["warning", "partial", "stale"].includes(normalized)) {
    return "badge badge-warn";
  }
  if (["error", "unavailable", "failed", "invalid"].includes(normalized)) {
    return "badge badge-err";
  }
  return "badge badge-neutral";
}
