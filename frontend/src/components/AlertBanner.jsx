import React from 'react';

function AlertBanner() {
  return (
    <div style={{ padding: '0.75rem 1.5rem', backgroundColor: '#1e293b', borderBottom: '1px solid #334155' }}>
      <p style={{ color: '#10b981', fontSize: '0.9rem' }}>
        <strong>System Status:</strong> Normal Monitoring (No Active Evacuation Triggers)
      </p>
    </div>
  );
}

export default AlertBanner;
