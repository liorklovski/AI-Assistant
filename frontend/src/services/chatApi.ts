import axios, { AxiosResponse } from 'axios';
import { MessageRequest, MessageJobResponse, MessageStatusResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout. Please try again.');
    }
    if (error.response?.status === 500) {
      throw new Error('Server error. Please try again later.');
    }
    if (error.response?.status === 404) {
      throw new Error('Service not found. Please check if the backend is running.');
    }
    throw error;
  }
);

export const chatApi = {
  // Health check
  async healthCheck(): Promise<any> {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Submit message and get job ID (MVP endpoint: POST /messages)
  async submitMessage(message: string): Promise<MessageJobResponse> {
    const response = await apiClient.post('/messages', {
      message,
    } as MessageRequest);
    return response.data;
  },

  // Upload file and get job ID (MVP endpoint: POST /files)
  async uploadFile(file: File): Promise<MessageJobResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Poll for job status and result (MVP endpoint: GET /messages/{id})
  async getJobStatus(jobId: string): Promise<MessageStatusResponse> {
    const response = await apiClient.get(`/messages/${jobId}`);
    return response.data;
  },

  // List all jobs (for debugging)
  async listJobs(): Promise<any> {
    const response = await apiClient.get('/messages');
    return response.data;
  },

  // Get chat history for persistence
  async getChatHistory(): Promise<any> {
    const response = await apiClient.get('/chat/history');
    return response.data;
  },

  // Clear all chat history
  async clearChatHistory(): Promise<void> {
    await apiClient.delete('/chat/clear');
  },

  // Delete job (cleanup)
  async deleteJob(jobId: string): Promise<void> {
    await apiClient.delete(`/messages/${jobId}`);
  },
};