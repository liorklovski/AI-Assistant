import React, { useEffect, useRef, useState } from 'react';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { FileUpload } from './FileUpload';
import { ErrorMessage } from './ErrorMessage';
import { Modal } from './Modal';
import { useChat } from '../hooks/useChat';

export const ChatContainer: React.FC = () => {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    uploadFile,
    clearChat,
    clearError,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showClearModal, setShowClearModal] = useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (message: string) => {
    sendMessage(message);
  };

  const handleFileUpload = (file: File) => {
    uploadFile(file);
  };

  const handleClearChat = () => {
    setShowClearModal(true);
  };

  const handleConfirmClear = () => {
    clearChat();
    setShowClearModal(false);
  };

  const handleCancelClear = () => {
    setShowClearModal(false);
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <h1>AI Chat Assistant MVP</h1>
        <button 
          onClick={handleClearChat}
          className="clear-button"
          disabled={isLoading}
        >
          Clear Chat
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <ErrorMessage
          message={error}
          onDismiss={clearError}
        />
      )}

      {/* Messages Area */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h2>Welcome to AI Chat MVP!</h2>
            <p>Send a message or upload a file to start chatting with the AI assistant.</p>
            <p><small>Messages and files are processed asynchronously with job-based polling.</small></p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-input-container">
        <div className="input-row">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={isLoading}
            placeholder={
              isLoading 
                ? "Processing..." 
                : "Type your message and press Enter..."
            }
          />
          <FileUpload
            onFileUpload={handleFileUpload}
            disabled={isLoading}
          />
        </div>
        {isLoading && (
          <div className="loading-indicator">
            Processing your request...
          </div>
        )}
      </div>

      {/* Clear Chat Modal */}
      <Modal
        isOpen={showClearModal}
        onClose={handleCancelClear}
        onConfirm={handleConfirmClear}
        title="Clear Chat History"
        message="Are you sure you want to clear all chat messages and files? This action will permanently delete your conversation history and cannot be undone. All uploaded files will also be removed from the system."
        confirmText="Yes, Clear Everything"
        cancelText="Keep My Chat"
      />
    </div>
  );
};