import { useState, useCallback, useEffect } from 'react';
import { ChatState, Message, JobStatus } from '../types';
import { chatApi } from '../services/chatApi';

const INITIAL_STATE: ChatState = {
  messages: [],
  isLoading: false,
  error: null,
};

const MAX_ATTEMPTS = 30; // Max 30 attempts (about 30 seconds with 1s intervals)

export const useChat = () => {
  const [state, setState] = useState<ChatState>(INITIAL_STATE);

  // Poll for job completion (defined first to avoid "use before declaration" error)
  const pollForJobCompletion = useCallback(async (jobId: string) => {
    let attempts = 0;

    const poll = async (): Promise<void> => {
      try {
        attempts++;
        const statusResponse = await chatApi.getJobStatus(jobId);
        
        // Update message in state
        setState(prev => ({
          ...prev,
          messages: prev.messages.map(msg => 
            msg.id === jobId 
              ? {
                  ...msg,
                  status: statusResponse.status,
                  ai_response: statusResponse.ai_response,
                  analysis_result: statusResponse.analysis_result,
                  completed_at: statusResponse.completed_at,
                  // Update file fields if it's a file job
                  ...(statusResponse.job_type === 'file' && {
                    original_filename: statusResponse.original_filename,
                    file_type: statusResponse.file_type,
                    file_size: statusResponse.file_size,
                  })
                }
              : msg
          ),
        }));

        // If job is still processing and we haven't exceeded max attempts, continue polling
        if ((statusResponse.status === 'pending' || statusResponse.status === 'processing') 
            && attempts < MAX_ATTEMPTS) {
          setTimeout(poll, 1000); // Poll every 1 second
        } else if (attempts >= MAX_ATTEMPTS && statusResponse.status !== 'done') {
          // Timeout handling
          setState(prev => ({
            ...prev,
            error: 'Request timed out. Please try again.',
            messages: prev.messages.map(msg => 
              msg.id === jobId 
                ? { 
                    ...msg, 
                    status: 'error' as JobStatus, 
                    ai_response: msg.type === 'message' ? 'Request timed out' : undefined,
                    analysis_result: msg.type === 'file' ? 'Request timed out' : undefined
                  }
                : msg
            ),
          }));
        }
      } catch (error) {
        // Handle API errors
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Error checking status',
          messages: prev.messages.map(msg => 
            msg.id === jobId 
              ? { 
                  ...msg, 
                  status: 'error' as JobStatus,
                  ai_response: msg.type === 'message' ? 'Error occurred' : undefined,
                  analysis_result: msg.type === 'file' ? 'Error occurred' : undefined
                }
              : msg
          ),
        }));
      }
    };

    poll();
  }, []);

  // Submit message and start polling for response
  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    setState(prev => ({ 
      ...prev, 
      isLoading: true, 
      error: null 
    }));

    try {
      // Step 1: Submit message and get job ID
      const jobResponse = await chatApi.submitMessage(message.trim());
      const jobId = jobResponse.job_id;

      // Create initial message object
      const newMessage: Message = {
        id: jobId,
        type: 'message',
        user_message: message.trim(),
        status: 'pending' as JobStatus,
        created_at: new Date().toISOString(),
      };

      // Add message to state
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, newMessage],
        isLoading: false,
      }));

      // Step 2: Start polling for status
      pollForJobCompletion(jobId);

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to send message',
        isLoading: false,
      }));
    }
  }, [pollForJobCompletion]);

  // Upload file and start polling for response
  const uploadFile = useCallback(async (file: File) => {
    if (!file) return;

    setState(prev => ({ 
      ...prev, 
      isLoading: true, 
      error: null 
    }));

    try {
      // Step 1: Upload file and get job ID
      const jobResponse = await chatApi.uploadFile(file);
      const jobId = jobResponse.job_id;

      // Create initial file message object
      const newMessage: Message = {
        id: jobId,
        type: 'file',
        original_filename: file.name,
        file_type: file.name.split('.').pop() || '',
        file_size: file.size,
        status: 'pending' as JobStatus,
        created_at: new Date().toISOString(),
      };

      // Add message to state
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, newMessage],
        isLoading: false,
      }));

      // Step 2: Start polling for status
      pollForJobCompletion(jobId);

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to upload file',
        isLoading: false,
      }));
    }
  }, [pollForJobCompletion]);

  // Export both sendMessage and uploadFile
  const sendContent = useCallback(async (content: string | File) => {
    if (typeof content === 'string') {
      return sendMessage(content);
    } else {
      return uploadFile(content);
    }
  }, [sendMessage, uploadFile]);

  // Always load previous conversation on page refresh
  // Clean start only happens when backend memory is empty (fresh server start)
  useEffect(() => {
    const loadChatHistory = async () => {
      try {
        const historyResponse = await chatApi.getChatHistory();
        if (historyResponse.success && historyResponse.messages.length > 0) {
          // Load all existing messages from backend memory
          setState(prev => ({
            ...prev,
            messages: historyResponse.messages,
          }));
        } else {
          // Starting clean - backend memory is empty
        }
      } catch (error) {
        // Start clean on any error - unable to load chat history
      }
    };

    loadChatHistory();
  }, []);

  // Clear all messages (both frontend and backend)
  const clearChat = useCallback(async () => {
    try {
      await chatApi.clearChatHistory();
      setState(INITIAL_STATE);
    } catch (error) {
      // Still clear frontend even if backend fails
      setState(INITIAL_STATE);
    }
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    sendMessage,
    uploadFile,
    sendContent,
    clearChat,
    clearError,
  };
};