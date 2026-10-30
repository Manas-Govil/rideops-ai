import React from 'react';
import { Sparkles, TrendingUp, Clock, AlertTriangle, Shield, Plane } from 'lucide-react';

const SUGGESTIONS = [
  {
    icon: TrendingUp,
    category: 'Revenue',
    text: 'Which pickup zones generated the highest revenue?',
  },
  {
    icon: Clock,
    category: 'Demand',
    text: 'What hours have the highest trip demand?',
  },
  {
    icon: Plane,
    category: 'Airports',
    text: 'What percentage of trips are airport trips?',
  },
  {
    icon: AlertTriangle,
    category: 'Anomalies',
    text: 'Which trips appear anomalous?',
  },
  {
    icon: Shield,
    category: 'Quality',
    text: 'What are the most common data-quality problems?',
  },
  {
    icon: Sparkles,
    category: 'Schema',
    text: 'What tables and views are available in the schema?',
  },
];

const SuggestedQuestions = ({ onSelectQuestion, disabled }) => {
  return (
    <div className="suggestions-container">
      <div className="suggestions-label">
        <Sparkles size={14} className="suggestions-icon" />
        <span>Suggested Operations Inquiries:</span>
      </div>
      <div className="suggestions-grid">
        {SUGGESTIONS.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              className="suggestion-pill"
              onClick={() => onSelectQuestion(item.text)}
              disabled={disabled}
              type="button"
            >
              <Icon size={14} className="pill-icon" />
              <span className="pill-category">[{item.category}]</span>
              <span className="pill-text">{item.text}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default SuggestedQuestions;
