import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface QuestionResponse {
  question: string;
  answer: string;
}

export interface UploadResponse {
  message: string;
  filename: string;
}

export type Metric = 
  | 'correctness'
  | 'context_adherence'
  | 'instruction_adherence'
  | 'chunk_attribution'
  | 'toxic_content'
  | 'tone'
  | 'completeness';

export const askQuestion = async (question: string, metrics: Metric[]): Promise<QuestionResponse> => {
  const response = await axios.post(`${API_BASE_URL}/ask_pdf`, {
    question,
    offline_evaluation: true,
    metrics
  });
  return response.data;
};

export const uploadPDF = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(`${API_BASE_URL}/upload_pdf`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}; 