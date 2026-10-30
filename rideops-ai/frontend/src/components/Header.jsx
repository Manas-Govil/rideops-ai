import React from 'react';
import { Activity, ShieldCheck, Database, FileText } from 'lucide-react';

const Header = ({ health, activeTab, setActiveTab }) => {
  const isHealthy = health?.status === 'healthy' && health?.database_connected;

  return (
    <header className="header-container">
      <div className="header-left">
        <div className="brand-logo">
          <ShieldCheck className="brand-icon" size={28} />
          <div>
            <h1 className="brand-title">RideOps AI</h1>
            <p className="brand-subtitle">Governed Mobility Intelligence</p>
          </div>
        </div>
      </div>

      <nav className="header-nav">
        <button
          className={`nav-tab ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          <Activity size={16} />
          <span>Mobility Analytics</span>
        </button>
        <button
          className={`nav-tab ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          <FileText size={16} />
          <span>Agent Audit Trail</span>
        </button>
        <button
          className={`nav-tab ${activeTab === 'schema' ? 'active' : ''}`}
          onClick={() => setActiveTab('schema')}
        >
          <Database size={16} />
          <span>Data Schema</span>
        </button>
      </nav>

      <div className="header-right">
        <div className={`status-pill ${isHealthy ? 'status-online' : 'status-offline'}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {isHealthy ? 'System Operational' : 'System Offline'}
          </span>
        </div>
        {health?.total_trips > 0 && (
          <div className="trips-badge">
            <span className="trips-count">{Number(health.total_trips).toLocaleString()}</span>
            <span className="trips-label">Trips Governed</span>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
