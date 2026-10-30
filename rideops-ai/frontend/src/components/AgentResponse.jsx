import React from 'react';
import { Bot, CheckCircle2, Cpu, Clock, Layers } from 'lucide-react';

const AGENT_META = {
  SQL_ANALYST_AGENT: {
    label: 'SQL Analyst Agent',
    color: '#3b82f6',
    bg: 'rgba(59, 130, 246, 0.12)',
    border: 'rgba(59, 130, 246, 0.3)',
    description: 'Autonomous NYC mobility & revenue analytics specialist',
  },
  DATA_QUALITY_AGENT: {
    label: 'Data Quality Agent',
    color: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.12)',
    border: 'rgba(245, 158, 11, 0.3)',
    description: 'Data hygiene & anomaly detection specialist',
  },
  HELP_AGENT: {
    label: 'Help / Schema Agent',
    color: '#10b981',
    bg: 'rgba(16, 185, 129, 0.12)',
    border: 'rgba(16, 185, 129, 0.3)',
    description: 'System documentation & data catalog guide',
  },
};

const formatMarkdown = (text) => {
  if (!text) return null;

  // Split lines to render clean paragraphs, lists, and headers
  const lines = text.split('\n');
  const elements = [];
  let tableRows = [];
  let inTable = false;

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    // Markdown Table Detection
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      inTable = true;
      if (!trimmed.includes('---')) {
        const cells = trimmed
          .split('|')
          .slice(1, -1)
          .map((c) => c.trim());
        tableRows.push(cells);
      }
      return;
    } else if (inTable) {
      inTable = false;
      if (tableRows.length > 0) {
        const headers = tableRows[0];
        const rows = tableRows.slice(1);
        elements.push(
          <div key={`table-${index}`} className="embedded-table-wrapper">
            <table className="embedded-table">
              <thead>
                <tr>
                  {headers.map((h, i) => (
                    <th key={i}>{h.replace(/\*\*/g, '').replace(/`/g, '')}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, rIdx) => (
                  <tr key={rIdx}>
                    {row.map((cell, cIdx) => (
                      <td key={cIdx}>{cell.replace(/\*\*/g, '').replace(/`/g, '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        tableRows = [];
      }
    }

    if (!trimmed) {
      elements.push(<div key={`space-${index}`} className="text-spacer" />);
      return;
    }

    if (trimmed.startsWith('### ')) {
      elements.push(
        <h3 key={index} className="resp-h3">
          {trimmed.replace('### ', '')}
        </h3>
      );
    } else if (trimmed.startsWith('#### ')) {
      elements.push(
        <h4 key={index} className="resp-h4">
          {trimmed.replace('#### ', '')}
        </h4>
      );
    } else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      const content = trimmed.substring(2);
      elements.push(
        <li key={index} className="resp-li">
          {renderFormattedInline(content)}
        </li>
      );
    } else {
      elements.push(
        <p key={index} className="resp-p">
          {renderFormattedInline(trimmed)}
        </p>
      );
    }
  });

  return elements;
};

const renderFormattedInline = (str) => {
  // Bold formatting **text**
  const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="resp-code">{part.slice(1, -1)}</code>;
    }
    return part;
  });
};

const AgentResponse = ({ response }) => {
  if (!response) return null;

  const agentMeta = AGENT_META[response.route] || {
    label: response.route || 'Agent',
    color: '#8b5cf6',
    bg: 'rgba(139, 92, 246, 0.12)',
    border: 'rgba(139, 92, 246, 0.3)',
    description: 'RideOps Specialized AI Agent',
  };

  return (
    <div className="agent-response-card">
      <div className="agent-header">
        <div className="agent-info">
          <div
            className="agent-avatar"
            style={{ backgroundColor: agentMeta.bg, borderColor: agentMeta.border }}
          >
            <Bot size={22} style={{ color: agentMeta.color }} />
          </div>
          <div>
            <div className="agent-title-row">
              <span
                className="agent-name-badge"
                style={{
                  color: agentMeta.color,
                  backgroundColor: agentMeta.bg,
                  borderColor: agentMeta.border,
                }}
              >
                <Cpu size={12} />
                {agentMeta.label}
              </span>
              <span className="status-badge-success">
                <CheckCircle2 size={12} />
                Query completed
              </span>
            </div>
            <p className="agent-desc">{agentMeta.description}</p>
          </div>
        </div>

        <div className="agent-telemetry">
          <div className="telemetry-item">
            <Clock size={13} />
            <span>{response.latency_ms ? `${response.latency_ms} ms` : '< 1s'}</span>
          </div>
          {response.row_count > 0 && (
            <div className="telemetry-item">
              <Layers size={13} />
              <span>{response.row_count} rows</span>
            </div>
          )}
        </div>
      </div>

      <div className="agent-body">
        <div className="response-content">
          {formatMarkdown(response.answer)}
        </div>
      </div>
    </div>
  );
};

export default AgentResponse;
