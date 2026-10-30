import React, { useState, useEffect } from 'react';
import { getAuditLogs } from '../services/api';
import { RefreshCw, Shield, Clock, Layers, AlertCircle, CheckCircle2, ChevronRight, ChevronDown } from 'lucide-react';

const AuditTrail = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAuditLogs(25);
      setLogs(data);
    } catch (err) {
      setError(err.message || 'Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const toggleRow = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="audit-section-container">
      <div className="section-header-row">
        <div>
          <h2 className="section-title">
            <Shield size={20} className="section-title-icon" />
            Agent Audit Trail & Compliance Ledger
          </h2>
          <p className="section-desc">
            Immutable log of all agent routing decisions, synthesized SQL, execution latencies, and security statuses stored in PostgreSQL (<code className="resp-code">rideops.agent_audit_log</code>).
          </p>
        </div>
        <button className="refresh-btn" onClick={fetchLogs} disabled={loading}>
          <RefreshCw size={15} className={loading ? 'spinner' : ''} />
          <span>Refresh Audit Trail</span>
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="audit-table-card">
        <div className="table-scroll-container">
          <table className="data-table audit-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th>Timestamp</th>
                <th>User Inquiry</th>
                <th>Agent Route</th>
                <th>Status</th>
                <th>Rows</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="empty-table-cell">
                    No audit records found. Execute a query to generate an audit event.
                  </td>
                </tr>
              )}
              {logs.map((log) => {
                const isExpanded = expandedId === log.audit_id;
                const isSuccess = log.execution_status === 'SUCCESS';
                const formattedTime = new Date(log.timestamp).toLocaleString();

                return (
                  <React.Fragment key={log.audit_id}>
                    <tr
                      className={`audit-row ${isExpanded ? 'expanded-row' : ''}`}
                      onClick={() => toggleRow(log.audit_id)}
                    >
                      <td className="expand-cell">
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </td>
                      <td className="timestamp-cell">
                        <Clock size={12} className="cell-icon" />
                        {formattedTime}
                      </td>
                      <td className="question-cell" title={log.user_question}>
                        {log.user_question}
                      </td>
                      <td>
                        <span className="route-tag">{log.agent_route || 'ROUTER'}</span>
                      </td>
                      <td>
                        <span className={`status-pill-small ${isSuccess ? 'pill-success' : 'pill-warning'}`}>
                          {isSuccess ? <CheckCircle2 size={11} /> : <AlertCircle size={11} />}
                          {log.execution_status}
                        </span>
                      </td>
                      <td>{log.rows_returned ?? 0}</td>
                      <td>{log.latency_ms ? `${log.latency_ms} ms` : '-'}</td>
                    </tr>
                    {isExpanded && (
                      <tr className="audit-detail-row">
                        <td colSpan={7}>
                          <div className="audit-detail-box">
                            <div className="detail-grid">
                              <div>
                                <span className="detail-label">Audit ID:</span>
                                <span className="detail-value">#{log.audit_id}</span>
                              </div>
                              <div>
                                <span className="detail-label">Route:</span>
                                <span className="detail-value">{log.agent_route}</span>
                              </div>
                              <div>
                                <span className="detail-label">Latency:</span>
                                <span className="detail-value">{log.latency_ms} ms</span>
                              </div>
                            </div>
                            {log.generated_sql && (
                              <div className="detail-sql-block">
                                <span className="detail-label">Executed Governed SQL:</span>
                                <pre className="sql-code-block">
                                  <code>{log.generated_sql}</code>
                                </pre>
                              </div>
                            )}
                            {log.answer && (
                              <div className="detail-answer-block">
                                <span className="detail-label">Agent Answer Preview:</span>
                                <p className="detail-answer-text">{log.answer.substring(0, 300)}...</p>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AuditTrail;
