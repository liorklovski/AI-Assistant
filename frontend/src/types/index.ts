export type JobStatus = 'pending' | 'processing' | 'done' | 'error';
export type JobType = 'message' | 'file';

export interface Message {
  id: string;
  type: JobType;
  user_message?: string;
  ai_response?: string;
  original_filename?: string;
  file_type?: string;
  file_size?: number;
  analysis_result?: string;
  status: JobStatus;
  created_at: string;
  completed_at?: string;
}

export interface MessageRequest {
  message: string;
}

export interface MessageJobResponse {
  job_id: string;
}

export interface MessageStatusResponse {
  job_id: string;
  status: JobStatus;
  job_type: JobType;
  user_message?: string;
  ai_response?: string;
  original_filename?: string;
  file_type?: string;
  file_size?: number;
  analysis_result?: string;
  created_at: string;
  completed_at?: string;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}