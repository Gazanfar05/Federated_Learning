const HospitalApi = (() => {
  const config = window.HOSPITAL_CONFIG;

  function buildUrl(endpoint) {
    const normalizedBase = config.apiBaseUrl.replace(/\/+$/, '');
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${normalizedBase}${normalizedEndpoint}`;
  }

  async function request(endpoint, options = {}) {
    const timeoutMs = options.timeoutMs ?? config.timeoutMs;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(buildUrl(endpoint), {
        method: options.method || 'GET',
        headers: {
          'Accept': 'application/json',
          ...(options.headers || {})
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      const contentType = response.headers.get('content-type') || '';
      const payload = contentType.includes('application/json') ? await response.json() : await response.text();

      if (!response.ok) {
        const detail = typeof payload === 'object' && payload ? payload.detail || payload.message || 'Request failed.' : payload;
        return {
          ok: false,
          status: response.status,
          error: detail,
          data: null,
          endpoint,
        };
      }

      return {
        ok: true,
        status: response.status,
        data: payload,
        endpoint,
      };
    } catch (error) {
      const message = error?.name === 'AbortError' ? 'Request timed out.' : (error?.message || 'Network request failed.');
      return {
        ok: false,
        status: 0,
        error: message,
        data: null,
        endpoint,
      };
    } finally {
      clearTimeout(timer);
    }
  }

  function safeText(value, fallback = 'Not available') {
    if (value === null || value === undefined || value === '') return fallback;
    if (typeof value === 'string') {
      const cleaned = value.replace(/[<>]/g, '');
      return cleaned || fallback;
    }
    return String(value);
  }

  function timestampLabel(value) {
    if (!value) return 'Unknown';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString([], {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  async function getHealth() {
    return request('/health');
  }

  async function getTrainingStatus() {
    return request('/training/status');
  }

  async function getModelMetadata() {
    return request('/training/model?client_id=hospital_01');
  }

  async function getMonitoringClients() {
    return request('/monitoring/clients');
  }

  async function getMonitoringRound() {
    return request('/monitoring/round');
  }

  async function getMonitoringMetrics() {
    return request('/monitoring/metrics');
  }

  async function getMonitoringPrivacy() {
    return request('/monitoring/privacy');
  }

  async function getMonitoringAnomalies() {
    return request('/monitoring/anomalies');
  }

  return {
    request,
    safeText,
    timestampLabel,
    getHealth,
    getTrainingStatus,
    getModelMetadata,
    getMonitoringClients,
    getMonitoringRound,
    getMonitoringMetrics,
    getMonitoringPrivacy,
    getMonitoringAnomalies,
  };
})();
