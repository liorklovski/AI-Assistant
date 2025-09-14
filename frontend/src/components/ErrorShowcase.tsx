import React, { useState } from 'react';
import { ErrorPreview } from './ErrorPreview';

interface ErrorShowcaseProps {
  onTriggerError?: (errorType: string, errorMessage: string) => void;
}

const DEMO_ERROR_TESTS = [
  {
    id: 'empty_message',
    name: 'Empty Message Test',
    description: 'Send an empty message to trigger validation error',
    action: () => ({ type: 'validation', message: 'Message cannot be empty' }),
    icon: '✍️'
  },
  {
    id: 'invalid_file',
    name: 'Invalid File Test', 
    description: 'Try uploading an .exe file to trigger security error',
    action: () => ({ type: 'file', message: 'File type .exe not supported. Allowed types: txt, pdf, docx, jpg, jpeg, png, csv, json' }),
    icon: '📁'
  },
  {
    id: 'large_file',
    name: 'Large File Test',
    description: 'Upload a file larger than 10MB to trigger size error',
    action: () => ({ type: 'file', message: 'File size (15,728,640 bytes) exceeds maximum allowed size (10,485,760 bytes)' }),
    icon: '📊'
  },
  {
    id: 'network_error',
    name: 'Network Error Test',
    description: 'Simulate network connection failure',
    action: () => ({ type: 'network', message: 'Network request failed. Please check your connection and try again.' }),
    icon: '🌐'
  },
  {
    id: 'ai_service_error',
    name: 'AI Service Test',
    description: 'Simulate AI service being unavailable',
    action: () => ({ type: 'ai_service', message: 'AI services are temporarily experiencing issues. Using backup response system.' }),
    icon: '🤖'
  },
  {
    id: 'rate_limit',
    name: 'Rate Limit Test',
    description: 'Simulate too many requests error',
    action: () => ({ type: 'rate_limit', message: 'Rate limit exceeded. Please wait 60 seconds before sending another message.' }),
    icon: '⏱️'
  }
];

export const ErrorShowcase: React.FC<ErrorShowcaseProps> = ({ onTriggerError }) => {
  const [isShowcaseOpen, setIsShowcaseOpen] = useState(false);
  const [activeTest, setActiveTest] = useState<string | null>(null);
  const [demonstrationMode, setDemonstrationMode] = useState(false);

  const handleTestError = (test: typeof DEMO_ERROR_TESTS[0]) => {
    const result = test.action();
    setActiveTest(test.id);
    
    if (onTriggerError) {
      onTriggerError(result.type, result.message);
    }

    // Auto-reset after 5 seconds
    setTimeout(() => {
      setActiveTest(null);
    }, 5000);
  };

  const toggleDemonstrationMode = () => {
    setDemonstrationMode(!demonstrationMode);
    if (!demonstrationMode) {
      setIsShowcaseOpen(true);
    }
  };

  return (
    <div className="error-showcase-container">
      {/* Demo Control Panel */}
      <div className="demo-control-panel">
        <button 
          className="demo-toggle-button"
          onClick={toggleDemonstrationMode}
        >
          {demonstrationMode ? '🎯' : '🛡️'} 
          {demonstrationMode ? ' Exit Demo Mode' : ' Error Handling Demo'}
        </button>
        
        {demonstrationMode && (
          <button 
            className="showcase-toggle-button"
            onClick={() => setIsShowcaseOpen(!isShowcaseOpen)}
          >
            {isShowcaseOpen ? '▼' : '▶'} Error Scenarios ({DEMO_ERROR_TESTS.length})
          </button>
        )}
      </div>

      {/* Error Testing Interface */}
      {demonstrationMode && isShowcaseOpen && (
        <div className="error-testing-interface">
          <div className="demo-header">
            <h3>🧪 Error Handling Demonstration</h3>
            <p>Click any test below to demonstrate robust error handling:</p>
          </div>

          <div className="error-tests-grid">
            {DEMO_ERROR_TESTS.map((test) => (
              <div 
                key={test.id}
                className={`error-test-card ${activeTest === test.id ? 'active' : ''}`}
                onClick={() => handleTestError(test)}
              >
                <div className="test-header">
                  <span className="test-icon">{test.icon}</span>
                  <span className="test-name">{test.name}</span>
                  {activeTest === test.id && (
                    <span className="active-indicator">●</span>
                  )}
                </div>
                <p className="test-description">{test.description}</p>
                
                {activeTest === test.id && (
                  <div className="test-result">
                    <div className="result-preview">
                      ✅ Error triggered! Check the error display above.
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="demo-info">
            <h4>🎯 What This Demonstrates:</h4>
            <ul>
              <li><strong>Input Validation</strong> - Empty messages and invalid data</li>
              <li><strong>File Security</strong> - Type restrictions and size limits</li>
              <li><strong>Network Resilience</strong> - Connection failure handling</li>
              <li><strong>Service Reliability</strong> - AI fallback mechanisms</li>
              <li><strong>Rate Limiting</strong> - Abuse prevention</li>
              <li><strong>User Experience</strong> - Clear, actionable error messages</li>
            </ul>
          </div>
        </div>
      )}

      {/* Error Preview Component */}
      {demonstrationMode && (
        <ErrorPreview />
      )}
    </div>
  );
};
