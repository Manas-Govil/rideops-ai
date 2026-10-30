import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import QuestionInput from './components/QuestionInput';
import SuggestedQuestions from './components/SuggestedQuestions';
import AgentResponse from './components/AgentResponse';
import ResultsTable from './components/ResultsTable';
import QueryGovernance from './components/QueryGovernance';
import Charts from './components/Charts';
import AuditTrail from './components/AuditTrail';
import SchemaPanel from './components/SchemaPanel';
import { queryRideOps, getHealth } from './services/api';
import { AlertCircle, Activity, Sparkles } from 'lucide-react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('analytics');
  const [health, setHealth] = useState(null);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  // Check health on initial load
  useEffect(() => {
    const checkSystemHealth = async () => {
      const data = await getHealth();
      setHealth(data);
    };
    checkSystemHealth();

    // Auto-run a starter question for initial dashboard population
    handleQuerySubmit('Which pickup zones generated the highest revenue?');
  }, []);

  const handleQuerySubmit = async (queryText) => {
    if (!queryText || !queryText.trim() || loading) return;

    setQuestion(queryText);
    setLoading(true);
    setError(null);

    try {
      const result = await queryRideOps(queryText);
      setResponse(result);
    } catch (err) {
      setError(err.message || 'An error occurred while communicating with the RideOps backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-layout">
      <Header
        health={health}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="main-content">
        {activeTab === 'analytics' && (
          <div className="analytics-view">
            <div className="inquiry-hero">
              <div className="inquiry-hero-text">
                <span className="hero-eyebrow">
                  <Activity size={14} /> NYC Operations Intelligence
                </span>
                <h2 className="hero-title">Natural Language Mobility Analytics</h2>
                <p className="hero-desc">
                  Ask natural questions across 3.47M taxi records. Requests are dynamically routed to specialized AI agents and protected by strict PostgreSQL guardrails.
                </p>
              </div>

              <QuestionInput
                question={question}
                setQuestion={setQuestion}
                onSubmit={handleQuerySubmit}
                loading={loading}
              />

              <SuggestedQuestions
                onSelectQuestion={handleQuerySubmit}
                disabled={loading}
              />
            </div>

            {error && (
              <div className="error-banner">
                <AlertCircle size={18} />
                <div className="error-content">
                  <strong>Query Execution Failed:</strong> {error}
                </div>
              </div>
            )}

            {response && (
              <div className="response-layout">
                {/* 1. Main Agent Response */}
                <AgentResponse response={response} />

                {/* 2. Visualizations / Charts (when data is chartable) */}
                {response.data && <Charts data={response.data} />}

                {/* 3. Structured Results Table */}
                {response.data && <ResultsTable data={response.data} />}

                {/* 4. Query Governance & Security Verification */}
                <QueryGovernance response={response} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'audit' && <AuditTrail />}

        {activeTab === 'schema' && <SchemaPanel />}
      </main>

      <footer className="footer-container">
        <div className="footer-left">
          <span>RideOps AI • Governed Multi-Agent Mobility Analytics System</span>
        </div>
        <div className="footer-right">
          <span>PostgreSQL 18.6 • FastAPI • 3,475,226 Ingested Trips</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
