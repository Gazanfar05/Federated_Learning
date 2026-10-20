import { hospitalConfig } from "../config/hospital-config.js";
import {
  renderEmpty,
  renderError,
  renderLoading,
  renderMetricGrid,
  renderStatusCards,
  renderTimeline,
  renderValidationTable,
  renderStaleBadge
} from "./state-components.js";
import { renderLineChart, renderStackedBars } from "./charts.js";
import { createElement, formatTimestamp } from "../utils/dom.js";

export class PortalController {
  constructor(apiService, settings) {
    this.api = apiService;
    this.settings = settings;
    this.lastUpdatedMs = 0;
    this.nodes = {
      overviewGrid: document.getElementById("overviewGrid"),
      latestEvalBlock: document.getElementById("latestEvalBlock"),
      validationHistoryBlock: document.getElementById("validationHistoryBlock"),
      validationWorkspace: document.getElementById("validationWorkspace"),
      featureQualityBlock: document.getElementById("featureQualityBlock"),
      featureQualityChart: document.getElementById("featureQualityChart"),
      evaluationLabSummary: document.getElementById("evaluationLabSummary"),
      evaluationHistoryChart: document.getElementById("evaluationHistoryChart"),
      comparisonBlock: document.getElementById("comparisonBlock"),
      comparisonChart: document.getElementById("comparisonChart"),
      timelineBlock: document.getElementById("timelineBlock"),
      staleBadge: document.getElementById("staleBadge")
    };
  }

  updateSettings(nextSettings) {
    this.settings = nextSettings;
    this.api.updateSettings(nextSettings);
    this.updateStaleBadge();
  }

  updateStaleBadge() {
    if (!this.lastUpdatedMs) {
      renderStaleBadge(this.nodes.staleBadge, "No data loaded", "badge badge-neutral");
      return;
    }

    const ageMs = Date.now() - this.lastUpdatedMs;
    if (ageMs > this.settings.staleDataMs) {
      renderStaleBadge(this.nodes.staleBadge, `Stale data (${Math.floor(ageMs / 1000)}s)`, "badge badge-warn");
      return;
    }

    renderStaleBadge(this.nodes.staleBadge, `Fresh (${Math.floor(ageMs / 1000)}s)`, "badge badge-ok");
  }

  async refreshOverview() {
    renderLoading(this.nodes.overviewGrid, "Loading core status...");
    renderLoading(this.nodes.latestEvalBlock, "Loading latest evaluation...");
    renderLoading(this.nodes.validationHistoryBlock, "Loading validation history...");

    const cards = [];

    let health;
    try {
      health = await this.api.getHealth();
      cards.push({ title: "Central API Connectivity", status: "ok", statusLabel: "Healthy", note: `Round ${health.round}, model version ${health.model_version}` });
    } catch (error) {
      cards.push({ title: "Central API Connectivity", status: "error", statusLabel: "Unavailable", note: error.message });
    }

    try {
      const model = await this.api.getModelCurrent();
      cards.push({ title: "Current Model Metadata", status: "available", statusLabel: "Available", note: `Version ${model.model_version}, round ${model.round_id}` });
    } catch (error) {
      cards.push({ title: "Current Model Metadata", status: "unavailable", statusLabel: "Unavailable", note: error.message });
    }

    try {
      const clients = await this.api.getMonitoringClients();
      const local = (clients.clients || []).find((item) => item.client_id === hospitalConfig.hospitalId);
      if (local) {
        cards.push({ title: "Local Validation Readiness", status: "partial", statusLabel: "Central-only", note: "Local dataset checks require hospital-local agent endpoints." });
      } else {
        cards.push({ title: "Local Validation Readiness", status: "warning", statusLabel: "Not observed", note: "hospital_02 is not visible in central monitoring clients list." });
      }
    } catch (error) {
      cards.push({ title: "Local Validation Readiness", status: "unavailable", statusLabel: "Unavailable", note: error.message });
    }

    cards.push({ title: "Feature-schema Status", status: "partial", statusLabel: "Pending local report", note: "Schema checks are displayed only after a hospital-local validation report is supplied." });
    cards.push({ title: "Dataset Validation Status", status: "partial", statusLabel: "Pending local report", note: "No validated local dataset summary received from agent endpoints." });

    renderStatusCards(this.nodes.overviewGrid, cards);

    try {
      const evaluation = await this.api.getEvaluationLatest();
      renderMetricGrid(this.nodes.latestEvalBlock, [
        { label: "Accuracy", value: String(evaluation.accuracy ?? "Unavailable") },
        { label: "Loss", value: String(evaluation.loss ?? "Unavailable") },
        { label: "Validation Samples", value: String(evaluation.validation_sample_count ?? "Unavailable") },
        { label: "Model Version", value: String(evaluation.model_version ?? "Unavailable") },
        { label: "Round", value: String(evaluation.round_number ?? "Unavailable") },
        { label: "Timestamp", value: formatTimestamp(evaluation.evaluation_timestamp) }
      ]);
    } catch (error) {
      renderEmpty(
        this.nodes.latestEvalBlock,
        "No local evaluation result",
        `Unavailable: ${error.message}. Genuine local evaluation metrics will appear when the hospital-local agent provides an approved aggregate summary.`
      );
    }

    try {
      const history = await this.api.getDatasetValidationHistory();
      if (!history.records || !history.records.length) {
        renderEmpty(this.nodes.validationHistoryBlock, "Validation history is empty", "No validated local history records have been provided yet.");
      } else {
        const rows = history.records.slice(0, 8).map((record) => ({
          label: formatTimestamp(record.timestamp),
          value: record.status || "Unknown"
        }));
        renderMetricGrid(this.nodes.validationHistoryBlock, rows);
      }
    } catch (error) {
      renderEmpty(
        this.nodes.validationHistoryBlock,
        "Validation history unavailable",
        `Unavailable: ${error.message}. This section will render only verified timeline records from a local source.`
      );
    }

    this.lastUpdatedMs = Date.now();
    this.updateStaleBadge();
  }

  async refreshValidation() {
    renderLoading(this.nodes.validationWorkspace, "Loading dataset validation workspace...");

    try {
      const report = await this.api.getDatasetValidationReport();
      const checks = [
        {
          name: "Required feature columns",
          status: report.required_feature_columns_check?.status || "unavailable",
          statusLabel: report.required_feature_columns_check?.status || "Unavailable",
          detail: report.required_feature_columns_check?.detail || "No local report"
        },
        {
          name: "Missing-value checks",
          status: report.missing_value_check?.status || "unavailable",
          statusLabel: report.missing_value_check?.status || "Unavailable",
          detail: report.missing_value_check?.detail || "No local report"
        },
        {
          name: "Numeric-type validation",
          status: report.numeric_type_check?.status || "unavailable",
          statusLabel: report.numeric_type_check?.status || "Unavailable",
          detail: report.numeric_type_check?.detail || "No local report"
        },
        {
          name: "Invalid target values",
          status: report.target_value_check?.status || "unavailable",
          statusLabel: report.target_value_check?.status || "Unavailable",
          detail: report.target_value_check?.detail || "No local report"
        },
        {
          name: "Duplicate detection",
          status: report.duplicate_detection?.status || "unavailable",
          statusLabel: report.duplicate_detection?.status || "Unavailable",
          detail: report.duplicate_detection?.detail || "Not supplied"
        },
        {
          name: "Sample count",
          status: report.sample_count?.status || "unavailable",
          statusLabel: report.sample_count?.status || "Unavailable",
          detail: report.sample_count?.detail || "No local report"
        },
        {
          name: "Class balance",
          status: report.class_balance?.status || "unavailable",
          statusLabel: report.class_balance?.status || "Unavailable",
          detail: report.class_balance?.detail || "No local report"
        },
        {
          name: "Train/validation split",
          status: report.split_info?.status || "unavailable",
          statusLabel: report.split_info?.status || "Unavailable",
          detail: report.split_info?.detail || "No local report"
        },
        {
          name: "Validation warnings",
          status: report.validation_warnings?.length ? "warning" : "ok",
          statusLabel: report.validation_warnings?.length ? "Warnings" : "None",
          detail: report.validation_warnings?.length ? report.validation_warnings.join(" | ") : "No warnings recorded"
        }
      ];
      renderValidationTable(this.nodes.validationWorkspace, checks);
    } catch (error) {
      const fallbackChecks = [
        "Required feature columns",
        "Missing-value checks",
        "Numeric-type validation",
        "Invalid target values",
        "Duplicate detection",
        "Sample count",
        "Class balance",
        "Train/validation split",
        "Validation warnings"
      ].map((name) => ({
        name,
        status: "unavailable",
        statusLabel: "Unavailable",
        detail: "Hospital-local validation report has not been supplied yet."
      }));
      renderValidationTable(this.nodes.validationWorkspace, fallbackChecks);
      const note = createElement("div", "error-state");
      note.appendChild(createElement("strong", "", "Validation report unavailable"));
      note.appendChild(createElement("p", "", error.message));
      this.nodes.validationWorkspace.appendChild(note);
    }
  }

  async refreshFeatureQuality() {
    renderLoading(this.nodes.featureQualityBlock, "Loading feature quality report...");
    renderLoading(this.nodes.featureQualityChart, "Loading feature quality visualization...");

    try {
      const report = await this.api.getFeatureQualityReport();
      renderMetricGrid(this.nodes.featureQualityBlock, [
        { label: "Feature completeness", value: String(report.feature_completeness ?? "Unavailable") },
        { label: "Valid vs invalid", value: String(report.valid_invalid_summary ?? "Unavailable") },
        { label: "Range warnings", value: String(report.range_warning_count ?? "Unavailable") },
        { label: "Schema compatibility", value: String(report.schema_compatibility ?? "Unavailable") },
        { label: "Validation summary", value: String(report.summary_status ?? "Unavailable") }
      ]);

      const rows = Array.isArray(report.features)
        ? report.features
            .filter((item) => Number.isFinite(item.valid_percent))
            .map((item) => ({ name: item.name || "Unnamed", validPercent: item.valid_percent }))
        : [];
      renderStackedBars(this.nodes.featureQualityChart, rows, {
        emptyText: "No feature-level percentages are available yet."
      });
    } catch (error) {
      renderEmpty(
        this.nodes.featureQualityBlock,
        "No feature quality report yet",
        `Local validation agent has not supplied feature quality aggregates. (${error.message})`
      );
      renderStackedBars(this.nodes.featureQualityChart, [], {
        emptyText: "Feature quality chart will render when approved aggregate feature metrics become available."
      });
    }
  }

  async refreshEvaluation() {
    renderLoading(this.nodes.evaluationLabSummary, "Loading evaluation summary...");
    renderLoading(this.nodes.evaluationHistoryChart, "Loading evaluation history...");

    try {
      const latest = await this.api.getEvaluationLatest();
      renderMetricGrid(this.nodes.evaluationLabSummary, [
        { label: "Accuracy", value: String(latest.accuracy ?? "Unavailable") },
        { label: "Loss", value: String(latest.loss ?? "Unavailable") },
        { label: "Validation sample count", value: String(latest.validation_sample_count ?? "Unavailable") },
        { label: "Model version", value: String(latest.model_version ?? "Unavailable") },
        { label: "Round number", value: String(latest.round_number ?? "Unavailable") },
        { label: "Evaluation timestamp", value: formatTimestamp(latest.evaluation_timestamp) }
      ]);
    } catch (error) {
      renderEmpty(this.nodes.evaluationLabSummary, "No genuine evaluation result", `Unavailable: ${error.message}.`);
    }

    try {
      const history = await this.api.getEvaluationHistory();
      const points = Array.isArray(history.records)
        ? history.records
            .filter((item) => Number.isFinite(item.accuracy))
            .map((item) => ({ label: formatTimestamp(item.evaluation_timestamp), value: item.accuracy }))
        : [];
      renderLineChart(this.nodes.evaluationHistoryChart, points, {
        emptyText: "No verified evaluation history records available for charting."
      });
    } catch (error) {
      renderLineChart(this.nodes.evaluationHistoryChart, [], {
        emptyText: `Evaluation history unavailable: ${error.message}`
      });
    }
  }

  async refreshComparison(leftVersion, rightVersion) {
    renderLoading(this.nodes.comparisonBlock, "Loading comparison...");
    renderLoading(this.nodes.comparisonChart, "Loading comparison chart...");

    if (!leftVersion || !rightVersion) {
      renderEmpty(this.nodes.comparisonBlock, "Comparison unavailable", "Enter two model versions or rounds to request a verified comparison.");
      renderLineChart(this.nodes.comparisonChart, [], {
        emptyText: "No verified comparison data available."
      });
      return;
    }

    try {
      const response = await this.api.getModelComparison(leftVersion, rightVersion);
      renderMetricGrid(this.nodes.comparisonBlock, [
        { label: "Left version", value: String(response.left_version ?? leftVersion) },
        { label: "Right version", value: String(response.right_version ?? rightVersion) },
        { label: "Left accuracy", value: String(response.left_accuracy ?? "Unavailable") },
        { label: "Right accuracy", value: String(response.right_accuracy ?? "Unavailable") },
        { label: "Left loss", value: String(response.left_loss ?? "Unavailable") },
        { label: "Right loss", value: String(response.right_loss ?? "Unavailable") }
      ]);

      const chartSeries = [];
      if (Number.isFinite(response.left_accuracy)) {
        chartSeries.push({ label: "left", value: response.left_accuracy });
      }
      if (Number.isFinite(response.right_accuracy)) {
        chartSeries.push({ label: "right", value: response.right_accuracy });
      }
      renderLineChart(this.nodes.comparisonChart, chartSeries, {
        emptyText: "No chartable comparison metrics in the verified response."
      });
    } catch (error) {
      renderEmpty(
        this.nodes.comparisonBlock,
        "Comparison data unavailable",
        `Unavailable: ${error.message}. This panel stays read-only until two genuine model summaries can be queried.`
      );
      renderLineChart(this.nodes.comparisonChart, [], {
        emptyText: "No verified comparison data available."
      });
    }
  }

  async refreshHistory() {
    renderLoading(this.nodes.timelineBlock, "Loading timeline...");

    try {
      const payload = await this.api.getTimelineEvents();
      if (!Array.isArray(payload.events) || payload.events.length === 0) {
        renderEmpty(
          this.nodes.timelineBlock,
          "Timeline is empty",
          "No verified dataset validation, model metadata, local evaluation, warning, or failure events were returned."
        );
        return;
      }

      const events = payload.events.map((event) => ({
        type: event.type || "Unknown",
        status: event.status || "Unknown",
        timestamp: formatTimestamp(event.timestamp),
        message: event.message || "No details provided."
      }));
      renderTimeline(this.nodes.timelineBlock, events);
    } catch (error) {
      renderEmpty(
        this.nodes.timelineBlock,
        "Timeline unavailable",
        `Unavailable: ${error.message}. Timeline will render only verified source events.`
      );
    }
  }

  async refreshAll() {
    await this.refreshOverview();
    await this.refreshValidation();
    await this.refreshFeatureQuality();
    await this.refreshEvaluation();
    await this.refreshHistory();
  }
}
