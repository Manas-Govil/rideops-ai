import React, { useState, useEffect } from 'react';
import { getSchema } from '../services/api';
import { Database, Table, Layers, ShieldCheck, RefreshCw, AlertCircle } from 'lucide-react';

const SchemaPanel = () => {
  const [schemaText, setSchemaText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSchema = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSchema();
      setSchemaText(data.schema || '');
    } catch (err) {
      setError(err.message || 'Failed to load schema documentation.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchema();
  }, []);

  return (
    <div className="schema-section-container">
      <div className="section-header-row">
        <div>
          <h2 className="section-title">
            <Database size={20} className="section-title-icon" />
            RideOps Governed Data Warehouse & Catalog
          </h2>
          <p className="section-desc">
            Direct catalog reflection from <code className="resp-code">GET /api/schema</code> detailing approved warehouse tables, materialized views, and security parameters.
          </p>
        </div>
        <button className="refresh-btn" onClick={fetchSchema} disabled={loading}>
          <RefreshCw size={15} className={loading ? 'spinner' : ''} />
          <span>Reload Catalog</span>
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="schema-grid">
        <div className="schema-card">
          <div className="schema-card-header">
            <Layers size={18} className="text-blue" />
            <h3>Analytical Views (Pre-Aggregated & Clean)</h3>
          </div>
          <div className="schema-object-list">
            <div className="schema-object-item">
              <span className="object-name">rideops.v_clean_trips</span>
              <span className="object-desc">Valid operational trips with anomalies filtered (<code className="resp-code">anomaly_flag = FALSE</code>) and resolved zone names.</span>
            </div>
            <div className="schema-object-item">
              <span className="object-name">rideops.v_hourly_demand</span>
              <span className="object-desc">Hourly demand patterns (0-23), total trips, revenue, average fare, and airport activity.</span>
            </div>
            <div className="schema-object-item">
              <span className="object-name">rideops.v_zone_performance</span>
              <span className="object-desc">Pickup zone metrics including total revenue, volume, fare-per-mile, and tip percentage.</span>
            </div>
            <div className="schema-object-item">
              <span className="object-name">rideops.v_quality_issue_summary</span>
              <span className="object-desc">Aggregated breakdown of data quality issues by severity and occurrence count.</span>
            </div>
          </div>
        </div>

        <div className="schema-card">
          <div className="schema-card-header">
            <Table size={18} className="text-emerald" />
            <h3>Core Warehouse Tables</h3>
          </div>
          <div className="schema-object-list">
            <div className="schema-object-item">
              <span className="object-name">rideops.dim_taxi_zones</span>
              <span className="object-desc">260 official spatial taxi zone boundaries, boroughs, and location IDs.</span>
            </div>
            <div className="schema-object-item">
              <span className="object-name">rideops.fact_trips</span>
              <span className="object-desc">3,475,226 raw & transformed trips with derived metrics and anomaly flags.</span>
            </div>
            <div className="schema-object-item">
              <span className="object-name">rideops.data_quality_issues</span>
              <span className="object-desc">887,904 audit records detailing specific financial and operational anomalies.</span>
            </div>
            <div className="schema-object-item">
              <span className="object-name">rideops.agent_audit_log</span>
              <span className="object-desc">Immutable compliance ledger tracking agent questions, SQL, and latencies.</span>
            </div>
          </div>
        </div>
      </div>

      <div className="schema-raw-card">
        <div className="schema-raw-header">
          <ShieldCheck size={16} className="text-blue" />
          <h4>Live Schema Response Payload (GET /api/schema)</h4>
        </div>
        <pre className="schema-raw-text">
          <code>{schemaText || (loading ? 'Loading catalog definition...' : 'No schema definition available.')}</code>
        </pre>
      </div>
    </div>
  );
};

export default SchemaPanel;
