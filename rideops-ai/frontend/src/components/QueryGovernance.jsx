import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, ChevronUp, Copy, Check, Lock, Database, Clock, Layers } from 'lucide-react';

const QueryGovernance = ({ response }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!response) return null;

  const { sql, route, row_count, latency_ms } = response;

  const copyToClipboard = () => {
    if (sql) {
      navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="governance-card">
      <div className="governance-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="governance-header-left">
          <ShieldCheck size={18} className="gov-icon" />
          <h4 className="gov-title">Query Governance & Security Verification</h4>
          <div className="gov-tags">
            <span className="gov-tag gov-tag-readonly">
              <Lock size={11} />
              Read-Only
            </span>
            <span className="gov-tag gov-tag-approved">
              <Database size={11} />
              Approved RideOps Schema
            </span>
            <span className="gov-tag gov-tag-guardrail">
              <ShieldCheck size={11} />
              Guardrails Enforced
            </span>
          </div>
        </div>

        <button className="toggle-btn" aria-label="Toggle governance details">
          {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      {isOpen && (
        <div className="governance-body">
          <div className="gov-metrics-grid">
            <div className="gov-metric-box">
              <span className="gov-metric-label">Agent Route</span>
              <span className="gov-metric-value">{route || 'UNKNOWN'}</span>
            </div>
            <div className="gov-metric-box">
              <span className="gov-metric-label">Execution Latency</span>
              <span className="gov-metric-value">{latency_ms ? `${latency_ms} ms` : 'N/A'}</span>
            </div>
            <div className="gov-metric-box">
              <span className="gov-metric-label">Rows Returned</span>
              <span className="gov-metric-value">{row_count ?? 0}</span>
            </div>
            <div className="gov-metric-box">
              <span className="gov-metric-label">Timeout Protection</span>
              <span className="gov-metric-value">5,000 ms</span>
            </div>
          </div>

          {sql ? (
            <div className="gov-sql-section">
              <div className="gov-sql-header">
                <span className="sql-label">Generated Governed SQL (PostgreSQL):</span>
                <button className="copy-sql-btn" onClick={copyToClipboard} title="Copy SQL">
                  {copied ? (
                    <>
                      <Check size={13} className="text-emerald" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={13} />
                      <span>Copy SQL</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="sql-code-block">
                <code>{sql.trim()}</code>
              </pre>
            </div>
          ) : (
            <div className="no-sql-message">
              <span>This inquiry was answered via system metadata / documentation catalog without issuing dynamic SQL.</span>
            </div>
          )}

          <div className="gov-compliance-notice">
            <span>🛡️ <strong>Governance Guarantee:</strong> Read-only SELECT policy enforced. DDL/DML write commands (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE) are blocked at the engine parser level.</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default QueryGovernance;
