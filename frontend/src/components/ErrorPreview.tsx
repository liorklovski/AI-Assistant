import React, { useState } from 'react';

type ErrorType = 'network' | 'validation' | 'file' | 'api' | 'rate_limit' | 'server' | 'ai_service';

interface ErrorScenario {
  type: ErrorType;
  title: string;
  message: string;
  code?: string;
  solution: string;
  severity: 'low' | 'medium' | 'high';
  icon: string;
}

const ERROR_SCENARIOS: ErrorScenario[] = [
  {
    type: 'network',
    title: 'Network Connection Error',
    message: 'Unable to connect to the server. Please check your internet connection.',
    code: 'NETWORK_ERROR',
    solution: 'Check your internet connection and try again',
    severity: 'high',
    icon: '🌐'
  },
  {
    type: 'validation',
    title: 'Message Validation Error',
    message: 'Message cannot be empty. Please enter a message to send.',
    code: 'VALIDATION_ERROR',
    solution: 'Enter a valid message and try again',
    severity: 'low',
    icon: '✍️'
  },
  {
    type: 'file',
    title: 'File Upload Error',
    message: 'File type not supported. Allowed types: .txt, .pdf, .docx, .jpg, .jpeg, .png, .csv, .json',
    code: 'UNSUPPORTED_FILE_TYPE',
    solution: 'Upload a file with a supported format',
    severity: 'medium',
    icon: '📁'
  },
  {
    type: 'api',
    title: 'AI Service Unavailable',
    message: 'AI services are temporarily unavailable. Our system is using backup responses.',
    code: 'AI_SERVICE_ERROR',
    solution: 'Your message was received. Try again in a few moments',
    severity: 'medium',
    icon: '🤖'
  },
  {
    type: 'rate_limit',
    title: 'Rate Limit Exceeded',
    message: 'Too many requests. Please wait a moment before sending another message.',
    code: 'RATE_LIMIT_EXCEEDED',
    solution: 'Wait 60 seconds and try again',
    severity: 'medium',
    icon: '⏱️'
  },
  {
    type: 'server',
    title: 'Server Error',
    message: 'An unexpected server error occurred. Our team has been notified.',
    code: 'INTERNAL_SERVER_ERROR',
    solution: 'Try again in a few minutes or contact support',
    severity: 'high',
    icon: '🔧'
  },
  {
    type: 'ai_service',
    title: 'AI Processing Error',
    message: 'AI processing failed after multiple attempts. Using fallback response.',
    code: 'AI_PROCESSING_FAILED',
    solution: 'Your message was processed with a backup system',
    severity: 'low',
    icon: '🧠'
  }
];

interface ErrorPreviewProps {
  onSelectError?: (scenario: ErrorScenario) => void;
  currentError?: string;
}

export const ErrorPreview: React.FC<ErrorPreviewProps> = ({ 
  onSelectError,
  currentError 
}) => {
  const [selectedError, setSelectedError] = useState<ErrorScenario | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleErrorSelect = (scenario: ErrorScenario) => {
    setSelectedError(scenario);
    if (onSelectError) {
      onSelectError(scenario);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return '#28a745';
      case 'medium': return '#ffc107';
      case 'high': return '#dc3545';
      default: return '#6c757d';
    }
  };

  return (
    <div className="error-preview-container">
      <div className="error-preview-header">
        <h3>🛡️ Error Handling Showcase</h3>
        <button 
          className="toggle-button"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '▼' : '▶'} {ERROR_SCENARIOS.length} Error Types
        </button>
      </div>

      {isExpanded && (
        <div className="error-scenarios-grid">
          {ERROR_SCENARIOS.map((scenario) => (
            <div 
              key={scenario.type}
              className={`error-scenario-card ${selectedError?.type === scenario.type ? 'selected' : ''}`}
              onClick={() => handleErrorSelect(scenario)}
            >
              <div className="error-scenario-header">
                <span className="error-icon">{scenario.icon}</span>
                <span 
                  className="error-severity-badge"
                  style={{ backgroundColor: getSeverityColor(scenario.severity) }}
                >
                  {scenario.severity.toUpperCase()}
                </span>
              </div>
              
              <h4 className="error-scenario-title">{scenario.title}</h4>
              <p className="error-scenario-message">{scenario.message}</p>
              
              {scenario.code && (
                <code className="error-code">Code: {scenario.code}</code>
              )}
              
              <div className="error-solution">
                <strong>Solution:</strong> {scenario.solution}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedError && (
        <div className="error-preview-demo">
          <h4>🎯 Live Error Preview:</h4>
          <div className={`error-message error-${selectedError.severity}`}>
            <div className="error-content">
              <div className="error-header">
                <span className="error-icon-large">{selectedError.icon}</span>
                <div className="error-details">
                  <div className="error-title">{selectedError.title}</div>
                  {selectedError.code && (
                    <div className="error-code-display">Error Code: {selectedError.code}</div>
                  )}
                </div>
                <span 
                  className="error-severity-indicator"
                  style={{ color: getSeverityColor(selectedError.severity) }}
                >
                  {selectedError.severity.toUpperCase()}
                </span>
              </div>
              
              <div className="error-body">
                <p className="error-message-text">{selectedError.message}</p>
                <div className="error-solution-box">
                  <strong>💡 How to resolve:</strong>
                  <p>{selectedError.solution}</p>
                </div>
              </div>
              
              <div className="error-actions">
                <button className="error-button primary">
                  Try Again
                </button>
                <button className="error-button secondary">
                  Get Help
                </button>
                <button 
                  className="error-button tertiary"
                  onClick={() => setSelectedError(null)}
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {currentError && !selectedError && (
        <div className="current-error-display">
          <h4>🚨 Current Application Error:</h4>
          <div className="error-message error-medium">
            <div className="error-content">
              <span className="error-text">⚠️ {currentError}</span>
              <div className="error-actions">
                <button className="error-button">
                  Retry
                </button>
                <button className="error-button">
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
