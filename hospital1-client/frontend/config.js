window.HOSPITAL_CONFIG = {
  hospitalId: 'hospital_01',
  institutionLabel: 'Clinical Research Unit',
  hospitalName: 'Hospital 01',
  defaultApiBaseUrl: 'https://127.0.0.1:8443',
  timeoutMs: 8000,
  staleAfterMs: 60000,
  ui: {
    theme: {
      navy: '#0d2340',
      teal: '#2a8c8d',
      cyan: '#4aa9c1',
      slate: '#63758a',
      ivory: '#f4f7f8',
      white: '#ffffff',
      border: '#dfeaf0'
    }
  }
};

window.HOSPITAL_CONFIG.apiBaseUrl = (() => {
  const params = new URLSearchParams(window.location.search);
  return params.get('api') || window.HOSPITAL_CONFIG.defaultApiBaseUrl;
})();
