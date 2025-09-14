import React from 'react';

interface ErrorMessageProps {
  message: string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export const ErrorMessage = ({ 
  message, 
  onDismiss, 
  onRetry 
}: ErrorMessageProps) => {
  return (
    <div className="error-message">
      <div className="error-content">
        <span className="error-text">⚠️ {message}</span>
        <div className="error-actions">
          {onRetry && (
            <button onClick={onRetry} className="error-button">
              Retry
            </button>
          )}
          
          {onDismiss && (
            <button onClick={onDismiss} className="error-button">
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  );
};