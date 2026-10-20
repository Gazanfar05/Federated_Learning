import { clearNode, createElement } from "../utils/dom.js";

function createSvg(width, height) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");
  return svg;
}

export function renderLineChart(container, series, options) {
  clearNode(container);
  if (!series || series.length < 2) {
    const empty = createElement("div", "empty-state", options.emptyText || "No historical records yet.");
    container.appendChild(empty);
    return;
  }

  const width = 760;
  const height = 240;
  const padding = 28;
  const values = series.map((item) => Number(item.value)).filter((value) => Number.isFinite(value));

  if (values.length < 2) {
    const empty = createElement("div", "empty-state", options.emptyText || "No chartable records yet.");
    container.appendChild(empty);
    return;
  }

  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const span = maxValue - minValue || 1;

  const points = series.map((item, index) => {
    const x = padding + (index / (series.length - 1)) * (width - padding * 2);
    const y = height - padding - ((Number(item.value) - minValue) / span) * (height - padding * 2);
    return `${x},${y}`;
  });

  const svg = createSvg(width, height);

  const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  line.setAttribute("fill", "none");
  line.setAttribute("stroke", "#22d3ee");
  line.setAttribute("stroke-width", "2");
  line.setAttribute("points", points.join(" "));
  svg.appendChild(line);

  points.forEach((point) => {
    const [x, y] = point.split(",");
    const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    dot.setAttribute("cx", x);
    dot.setAttribute("cy", y);
    dot.setAttribute("r", "3");
    dot.setAttribute("fill", "#4ba3ff");
    svg.appendChild(dot);
  });

  container.appendChild(svg);
}

export function renderStackedBars(container, rows, options) {
  clearNode(container);
  if (!rows || !rows.length) {
    const empty = createElement("div", "empty-state", options.emptyText || "No feature report available.");
    container.appendChild(empty);
    return;
  }

  const wrap = createElement("div", "metric-grid");
  rows.forEach((row) => {
    const bar = createElement("div", "metric");
    const label = createElement("p", "label", row.name);
    const visual = createElement("div", "");
    visual.style.display = "grid";
    visual.style.gridTemplateColumns = `${row.validPercent}% ${100 - row.validPercent}%`;
    visual.style.border = "1px solid rgba(101,151,206,0.35)";
    visual.style.borderRadius = "8px";
    visual.style.overflow = "hidden";

    const valid = createElement("div", "");
    valid.style.background = "rgba(39,210,141,0.7)";
    valid.style.height = "16px";

    const invalid = createElement("div", "");
    invalid.style.background = "rgba(255,108,132,0.7)";
    invalid.style.height = "16px";

    const caption = createElement("p", "value", `${row.validPercent.toFixed(1)}% valid`);

    visual.appendChild(valid);
    visual.appendChild(invalid);
    bar.appendChild(label);
    bar.appendChild(visual);
    bar.appendChild(caption);
    wrap.appendChild(bar);
  });
  container.appendChild(wrap);
}
