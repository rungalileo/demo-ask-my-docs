import { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  Stack,
} from '@mui/material';
import { useQA } from '../hooks/useQA';
import { uploadPDF, Metric } from '../services/api';

const AVAILABLE_METRICS: Metric[] = [
  'correctness',
  'context_adherence',
  'instruction_adherence',
  'chunk_attribution',
  'toxic_content',
  'tone',
  'completeness'
];

export const QAInterface = () => {
  const [question, setQuestion] = useState('');
  const [selectedMetrics, setSelectedMetrics] = useState<Metric[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<{
    loading: boolean;
    error: string | null;
    success: boolean;
  }>({
    loading: false,
    error: null,
    success: false,
  });
  const { askQuestion, isLoading, error, data } = useQA();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadStatus({ loading: true, error: null, success: false });
    try {
      await uploadPDF(selectedFile);
      setUploadStatus({ loading: false, error: null, success: true });
    } catch (err) {
      setUploadStatus({
        loading: false,
        error: 'Failed to upload PDF. Please try again.',
        success: false,
      });
    }
  };

  const handleMetricClick = (metric: Metric) => {
    setSelectedMetrics(prev => 
      prev.includes(metric)
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
      askQuestion(question, selectedMetrics);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Ask My Docs
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Upload PDF
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Button
            variant="contained"
            component="label"
            disabled={uploadStatus.loading}
          >
            Select PDF
            <input
              type="file"
              hidden
              accept=".pdf"
              onChange={handleFileChange}
            />
          </Button>
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={!selectedFile || uploadStatus.loading}
          >
            {uploadStatus.loading ? (
              <CircularProgress size={24} />
            ) : (
              'Upload'
            )}
          </Button>
        </Box>
        {selectedFile && (
          <Typography variant="body2" sx={{ mb: 1 }}>
            Selected file: {selectedFile.name}
          </Typography>
        )}
        {uploadStatus.error && (
          <Alert severity="error" sx={{ mt: 1 }}>
            {uploadStatus.error}
          </Alert>
        )}
        {uploadStatus.success && (
          <Alert severity="success" sx={{ mt: 1 }}>
            PDF uploaded successfully!
          </Alert>
        )}
      </Paper>
      
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Select Evaluation Metrics
        </Typography>
        <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'nowrap', overflowX: 'auto', gap: 1, py: 1 }}>
          {AVAILABLE_METRICS.map((metric) => (
            <Chip
              key={metric}
              label={metric.replace('_', ' ')}
              onClick={() => handleMetricClick(metric)}
              color={selectedMetrics.includes(metric) ? 'primary' : 'default'}
              variant={selectedMetrics.includes(metric) ? 'filled' : 'outlined'}
              size="small"
              sx={{
                minWidth: 'fit-content',
                backgroundColor: selectedMetrics.includes(metric) 
                  ? {
                      'correctness': '#4caf50',
                      'context_adherence': '#2196f3',
                      'instruction_adherence': '#9c27b0',
                      'chunk_attribution': '#ff9800',
                      'toxic_content': '#f44336',
                      'tone': '#00bcd4',
                      'completeness': '#ff4081'
                    }[metric]
                  : 'transparent',
                '&:hover': {
                  backgroundColor: selectedMetrics.includes(metric) 
                    ? {
                        'correctness': '#388e3c',
                        'context_adherence': '#1976d2',
                        'instruction_adherence': '#7b1fa2',
                        'chunk_attribution': '#f57c00',
                        'toxic_content': '#d32f2f',
                        'tone': '#0097a7',
                        'completeness': '#f50057'
                      }[metric]
                    : 'rgba(0, 0, 0, 0.04)'
                }
              }}
            />
          ))}
        </Stack>

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Ask a question about the PDF"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isLoading || !uploadStatus.success}
            sx={{ mb: 2 }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={isLoading || !question.trim() || !uploadStatus.success}
            fullWidth
          >
            {isLoading ? <CircularProgress size={24} /> : 'Ask Question'}
          </Button>
        </form>
      </Paper>

      {error && (
        <Paper elevation={3} sx={{ p: 2, mb: 2, bgcolor: '#fff3f3' }}>
          <Typography color="error">
            Error: {error.message}
          </Typography>
        </Paper>
      )}

      {data && (
        <Paper elevation={3} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Answer:
          </Typography>
          <Typography>{data.answer}</Typography>
        </Paper>
      )}
    </Box>
  );
}; 