import React from 'react';
import './App.css';
import AlertBanner from './components/AlertBanner';
import MapView from './components/MapView';
import EvacuationPanel from './components/EvacuationPanel';
import HazardMetrics from './components/HazardMetrics';

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Intelligent Disaster Decision-Support Platform</h1>
        <p>Multi-Hazard Risk Assessment & Dynamic Evacuation</p>
      </header>
      <AlertBanner />
      <main className="dashboard-grid">
        <section className="map-section">
          <MapView />
        </section>
        <aside className="control-sidebar">
          <HazardMetrics />
          <EvacuationPanel />
        </aside>
      </main>
    </div>
  );
}

export default App;
