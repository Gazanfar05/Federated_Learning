const HospitalPortal = (() => {
  const config = window.HOSPITAL_CONFIG;

  const state = {
    health: null,
    trainingStatus: null,
    model: null,
    clientMonitor: null,
    roundStatus: null,
    metrics: null,
    privacy: null,
    anomalies: null,
    loading: {
      health: false,
      trainingStatus: false,
      model: false,
      secondary: false,
    },
    lastUpdated: null,
  };

  const sections = {
    overview: document.getElementById('overview-section'),
    globalModel: document.getElementById('global-model-section'),
    dataset: document.getElementById('dataset-section'),
    training: document.getElementById('training-section'),
    evaluation: document.getElementById('evaluation-section'),
    updateReview: document.getElementById('update-review-section'),
    activityHistory: document.getElementById('activity-history-section'),
  };

  function setLoading(key, value) {
    state.loading[key] = value;
    const target = document.getElementById(`loading-${key}`);
    if (!target) return;
    target.innerHTML = value
      ? '<span class="loading-box"><span class="spinner"></span>Loading…</span>'
      : '';
  }

  function renderOverview() {
    const health = state.health?.data || {};
    const model = state.model?.data || {};
    const training = state.trainingStatus?.data || {};
    const recentActivity = buildRecentActivity();

    const summaryCards = [
      {
        label: 'Server',
        value: health.status === 'healthy' ? 'Reachable' : 'Unavailable',
        detail: health.status === 'healthy' ? 'Central health probe succeeded' : 'Awaiting server response',
      },
      {
        label: 'Federation',
        value: training.status || 'Pending',
        detail: training.current_round ? `Round ${training.current_round}` : 'No active round reported',
      },
      {
        label: 'Model',
        value: model.model_version ? `v${model.model_version}` : 'Not available',
        detail: model.round_id ? `Round ${model.round_id}` : 'Metadata pending',
      },
      {
        label: 'Dataset',
        value: state.datasetStatus || 'Pending',
        detail: state.datasetStatus === 'Validated' ? 'Local validation completed' : 'Validation service not connected',
      }
    ];

    const cardsHtml = summaryCards.map((card) => `
      <article class="card stat-card">
        <span class="label">${card.label}</span>
        <span class="value">${HospitalApi.safeText(card.value)}</span>
        <span class="small">${HospitalApi.safeText(card.detail)}</span>
      </article>
    `).join('');

    const overviewPanel = document.getElementById('overview-grid');
    overviewPanel.innerHTML = cardsHtml;

    const info = document.getElementById('overview-info');
    info.innerHTML = `
      ${UI.infoRow('Hospital', config.hospitalName, false)}
      ${UI.infoRow('Institution', config.institutionLabel, false)}
      ${UI.infoRow('Central server', health.status === 'healthy' ? 'Connected' : 'Unavailable', false)}
      ${UI.infoRow('Federation status', training.status || 'Not reported', false)}
      ${UI.infoRow('Current model version', model.model_version ? `v${model.model_version}` : 'Not available', false)}
      ${UI.infoRow('Current round', model.round_id ? `Round ${model.round_id}` : 'Not available', false)}
      ${UI.infoRow('Dataset readiness', state.datasetStatus || 'Pending', false)}
      ${UI.infoRow('Most recent operation', state.lastOperation || 'No operation recorded', false)}
    `;

    const activityTarget = document.getElementById('overview-activity');
    if (!recentActivity.length) {
      activityTarget.innerHTML = UI.emptyState('No recent activity', 'Real operation history will appear here when the backend provides it.');
      return;
    }
    activityTarget.innerHTML = recentActivity.map(UI.timelineItem).join('');
  }

  function renderGlobalModel() {
    const model = state.model?.data || {};
    const modelSection = document.getElementById('model-info');
    const artifactState = model.update_hash ? 'Metadata available' : 'Metadata unavailable';
    const integrityState = model.update_hash ? 'Not verified; digest present only in metadata' : 'Integrity not available';

    modelSection.innerHTML = `
      ${UI.infoRow('Model version', model.model_version ? `v${model.model_version}` : 'Unavailable')}
      ${UI.infoRow('Associated round', model.round_id ? `Round ${model.round_id}` : 'Unavailable')}
      ${UI.infoRow('Architecture', HospitalApi.safeText(model.architecture || 'Pending'))}
      ${UI.infoRow('Artifact availability', artifactState)}
      ${UI.infoRow('Integrity verification', integrityState)}
    `;
  }

  function renderDatasetSection() {
    const datasetTarget = document.getElementById('dataset-info');
    const dataset = state.datasetReport || {};
    const hasValidation = dataset && typeof dataset === 'object' && Object.keys(dataset).length > 0;

    if (!hasValidation) {
      datasetTarget.innerHTML = `
        ${UI.infoRow('Local dataset validation status', 'Dataset validation service not yet connected.')}
        ${UI.infoRow('Feature-schema validation', 'Not available')}
        ${UI.infoRow('Sample count', 'Unavailable')}
        ${UI.infoRow('Missing-value summary', 'Not implemented')}
        ${UI.infoRow('Validation warnings', 'None reported')}
      `;
      return;
    }

    datasetTarget.innerHTML = `
      ${UI.infoRow('Local dataset validation status', HospitalApi.safeText(dataset.status || 'Unknown'))}
      ${UI.infoRow('Feature-schema validation', HospitalApi.safeText(dataset.feature_schema_valid || 'Not available'))}
      ${UI.infoRow('Sample count', HospitalApi.safeText(dataset.sample_count || 'Unavailable'))}
      ${UI.infoRow('Missing-value summary', HospitalApi.safeText(dataset.missing_values || 'Not implemented'))}
      ${UI.infoRow('Validation warnings', HospitalApi.safeText(dataset.warnings || 'None'))}
    `;
  }

  function renderTrainingSection() {
    const target = document.getElementById('training-info');
    target.innerHTML = `
      ${UI.infoRow('Training job ID', 'Pending backend integration', 'muted')}
      ${UI.infoRow('Current operation status', 'OpenFL training integration pending', 'muted')}
      ${UI.infoRow('Genuine training progress', 'Unavailable', 'muted')}
      ${UI.infoRow('Local loss and evaluation metrics', 'Unavailable', 'muted')}
      ${UI.infoRow('Failure messages', 'None reported', 'muted')}
      ${UI.infoRow('Operation timestamps', 'Unavailable', 'muted')}
    `;

    const note = document.getElementById('training-note');
    note.innerHTML = `
      <div class="note-panel">
        <strong>Training workspace status</strong>
        <p>The local OpenFL training pipeline is not yet connected to this hospital frontend. This section is intentionally read-only and will display authentic job metadata and metrics when backend integration is available.</p>
      </div>
    `;
  }

  function renderEvaluationSection() {
    const target = document.getElementById('evaluation-info');
    target.innerHTML = `
      ${UI.infoRow('Accuracy', 'Pending genuine evaluation output')}
      ${UI.infoRow('Loss', 'Pending genuine evaluation output')}
      ${UI.infoRow('Validation sample count', 'Unavailable')}
      ${UI.infoRow('Evaluation round', 'Not available')}
      ${UI.infoRow('Model version', state.model?.data?.model_version ? `v${state.model.data.model_version}` : 'Not available')}
    `;
  }

  function renderUpdateReview() {
    const target = document.getElementById('update-review-info');
    target.innerHTML = `
      ${UI.infoRow('Base-model version', 'Pending backend data')}
      ${UI.infoRow('Training-job identifier', 'Not available')}
      ${UI.infoRow('Update artifact status', 'Not yet transmitted')}
      ${UI.infoRow('Update digest', 'Unavailable')}
      ${UI.infoRow('Submission status', 'Read-only placeholder; submission not implemented')}
    `;
  }

  function renderActivityHistory() {
    const target = document.getElementById('activity-list');
    const events = state.activityEvents || [];

    if (!events.length) {
      target.innerHTML = UI.emptyState('No activity events available', 'The backend has not supplied real operation history for this hospital yet.');
      return;
    }

    target.innerHTML = events.map(UI.timelineItem).join('');
  }

  function buildRecentActivity() {
    const events = state.activityEvents || [];
    return events.slice(0, 4);
  }

  function updateLastOperation() {
    const operations = [
      state.health?.data && state.health.ok ? 'Server health check' : null,
      state.model?.data ? 'Model metadata request' : null,
      state.trainingStatus?.data ? 'Training status request' : null,
    ].filter(Boolean);

    state.lastOperation = operations[operations.length - 1] || 'No operation recorded';
  }

  async function fetchAll() {
    setLoading('health', true);
    setLoading('trainingStatus', true);
    setLoading('model', true);
    setLoading('secondary', true);

    const [health, trainingStatus, model, clientMonitor, roundStatus, metrics, privacy, anomalies] = await Promise.all([
      HospitalApi.getHealth(),
      HospitalApi.getTrainingStatus(),
      HospitalApi.getModelMetadata(),
      HospitalApi.getMonitoringClients(),
      HospitalApi.getMonitoringRound(),
      HospitalApi.getMonitoringMetrics(),
      HospitalApi.getMonitoringPrivacy(),
      HospitalApi.getMonitoringAnomalies(),
    ]);

    state.health = health;
    state.trainingStatus = trainingStatus;
    state.model = model;
    state.clientMonitor = clientMonitor;
    state.roundStatus = roundStatus;
    state.metrics = metrics;
    state.privacy = privacy;
    state.anomalies = anomalies;
    state.lastUpdated = new Date().toISOString();

    state.datasetStatus = 'Dataset validation service not yet connected.';
    state.datasetReport = null;
    state.activityEvents = [
      {
        title: 'Portal initialized',
        description: 'Hospital 01 front-end loaded in local-only mode.',
        status: 'INFO',
        timestamp: new Date().toISOString(),
      }
    ];

    updateLastOperation();
    renderOverview();
    renderGlobalModel();
    renderDatasetSection();
    renderTrainingSection();
    renderEvaluationSection();
    renderUpdateReview();
    renderActivityHistory();

    setLoading('health', false);
    setLoading('trainingStatus', false);
    setLoading('model', false);
    setLoading('secondary', false);
  }

  function bindActions() {
    document.getElementById('retry-btn')?.addEventListener('click', fetchAll);
  }

  function init() {
    bindActions();
    renderOverview();
    renderGlobalModel();
    renderDatasetSection();
    renderTrainingSection();
    renderEvaluationSection();
    renderUpdateReview();
    renderActivityHistory();
    fetchAll();
  }

  return {
    init,
  };
})();

document.addEventListener('DOMContentLoaded', () => {
  HospitalPortal.init();
});
