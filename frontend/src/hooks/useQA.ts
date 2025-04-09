import { useMutation } from '@tanstack/react-query';
import { askQuestion, QuestionResponse, Metric } from '../services/api';

export const useQA = () => {
  const mutation = useMutation<QuestionResponse, Error, { question: string; metrics: Metric[] }>({
    mutationFn: ({ question, metrics }) => askQuestion(question, metrics),
  });

  return {
    askQuestion: (question: string, metrics: Metric[]) => mutation.mutate({ question, metrics }),
    isLoading: mutation.isPending,
    error: mutation.error,
    data: mutation.data,
  };
}; 