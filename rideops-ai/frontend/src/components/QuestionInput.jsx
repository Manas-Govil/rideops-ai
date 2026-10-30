import React from 'react';
import { Search, Loader2, ArrowRight } from 'lucide-react';

const QuestionInput = ({ question, setQuestion, onSubmit, loading }) => {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!loading && question.trim()) {
        onSubmit(question);
      }
    }
  };

  return (
    <form className="question-form" onSubmit={(e) => { e.preventDefault(); onSubmit(question); }}>
      <div className="input-wrapper">
        <Search className="search-icon" size={20} />
        <input
          type="text"
          className="question-input"
          placeholder="Ask a mobility question (e.g., Which pickup zones generated the highest revenue?)"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          type="submit"
          className="submit-btn"
          disabled={loading || !question.trim()}
        >
          {loading ? (
            <>
              <Loader2 className="spinner" size={18} />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <span>Ask RideOps</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>
      {loading && (
        <div className="loading-status-bar">
          <Loader2 className="spinner-subtle" size={14} />
          <span>Routing request to specialized agent & applying SQL guardrails...</span>
        </div>
      )}
    </form>
  );
};

export default QuestionInput;
