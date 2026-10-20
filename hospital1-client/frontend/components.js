const UI = (() => {
  function statusBadge(status, tone = 'neutral') {
    const map = {
      healthy: 'success',
      connected: 'success',
      available: 'success',
      warning: 'warning',
      pending: 'warning',
      unavailable: 'danger',
      error: 'danger',
      neutral: 'neutral',
    };

    const color = map[tone] || map[status?.toLowerCase?.()] || 'neutral';
    return `<span class="status-badge ${color}">${status}</span>`;
  }

  function infoRow(label, value, muted = false) {
    return `
      <div class="info-row ${muted ? 'muted' : ''}">
        <span class="label">${label}</span>
        <strong class="value">${value}</strong>
      </div>
    `;
  }

  function emptyState(message, detail = '') {
    return `
      <div class="empty-state">
        <div class="empty-icon">—</div>
        <h4>${message}</h4>
        ${detail ? `<p>${detail}</p>` : ''}
      </div>
    `;
  }

  function timelineItem(item) {
    const status = item.status || 'UNKNOWN';
    const tone = status.toLowerCase().includes('error') || status.toLowerCase().includes('failed') ? 'danger' :
      status.toLowerCase().includes('success') || status.toLowerCase().includes('completed') ? 'success' : 'neutral';

    return `
      <div class="timeline-item">
        <div class="timeline-dot ${tone}"></div>
        <div class="timeline-content">
          <div class="timeline-header">
            <strong>${HospitalApi.safeText(item.title || 'Activity')}</strong>
            ${statusBadge(status, tone)}
          </div>
          <p>${HospitalApi.safeText(item.description || 'No description provided.')}</p>
          <time>${HospitalApi.timestampLabel(item.timestamp || item.created_at || item.time)}</time>
        </div>
      </div>
    `;
  }

  return {
    statusBadge,
    infoRow,
    emptyState,
    timelineItem,
  };
})();
