fetch('https://qentis.duckdns.org/api/admin/stats/')
  .then(res => res.json())
  .then(data => {
    const items = document.getElementById('stat-items');
    const institutions = document.getElementById('stat-institutions');
    const verifications = document.getElementById('stat-accuracy');

    if (items && data.recent_registrations !== undefined) {
      items.textContent = data.recent_registrations + '+';
    }
    if (institutions && data.total_activity_logs !== undefined) {
      institutions.textContent = data.total_activity_logs + '+';
    }
  })
  .catch(() => {
    // keep hardcoded fallback values if API fails
  });