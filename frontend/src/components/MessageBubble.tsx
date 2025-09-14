import React from 'react';
import { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const timestamp = new Date(message.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'pending':
        return '⏳ Pending...';
      case 'processing':
        return '🔄 Processing...';
      case 'done':
        return '✅ Complete';
      case 'error':
        return '❌ Error';
      default:
        return status;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="message-container">
      {/* User Message or File */}
      <div className="message user-message">
        <div className="message-content">
          <strong>You:</strong> 
          {message.type === 'message' ? (
            <span> {message.user_message}</span>
          ) : (
            <span className="file-info">
              <span className="file-icon">📎</span>
              {message.original_filename}
              {message.file_size && (
                <span className="file-size"> ({formatFileSize(message.file_size)})</span>
              )}
            </span>
          )}
        </div>
        <div className="message-meta">
          {timestamp} | {getStatusDisplay(message.status)}
        </div>
      </div>

      {/* AI Response */}
      {(message.ai_response || message.analysis_result) && (
        <div className="message ai-message">
          <div className="message-content">
            <strong>AI:</strong> {message.ai_response || message.analysis_result}
          </div>
          {message.completed_at && (
            <div className="message-meta">
              {new Date(message.completed_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          )}
        </div>
      )}

      {/* Processing State */}
      {(message.status === 'processing' || message.status === 'pending') && 
       !message.ai_response && !message.analysis_result && (
        <div className="message ai-message processing">
          <div className="message-content">
            <strong>AI:</strong> {getStatusDisplay(message.status)}
          </div>
        </div>
      )}
    </div>
  );
};