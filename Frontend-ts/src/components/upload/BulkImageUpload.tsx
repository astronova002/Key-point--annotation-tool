import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Button,
  LinearProgress,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
  Alert,
  Link
} from '@mui/material';
import { Delete, Upload, CheckCircle, Error as ErrorIcon, Pending, PlayArrow } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { apiConfig } from '../../config/api';

interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
  annotations?: any[];
}

interface UploadProgress {
  total: number;
  uploaded: number;
  processed: number;
  failed: number;
}

const BulkImageUpload: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    total: 0,
    uploaded: 0,
    processed: 0,
    failed: 0
  });
  const [batchId, setBatchId] = useState<string | null>(null);
  const [uploadComplete, setUploadComplete] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map(file => ({
      file,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      status: 'pending',
      progress: 0
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    },
    multiple: true,
    maxFiles: 5000
  });

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const getAuthToken = () => {
    if (!isAuthenticated || !user) {
      console.error('User not authenticated');
      return null;
    }

    const token = user.accessToken;
    if (!token) {
      console.error('No access token found in user object');
      console.log('User object:', user);
      return null;
    }

    return token;
  };

  const startUpload = async () => {
    if (files.length === 0) return;

    const authToken = getAuthToken();
    if (!authToken) {
        alert('Please log in to upload files');
        return;
    }

    console.log('✅ Using valid auth token for upload');

    setIsUploading(true);
    setUploadProgress({
        total: files.length,
        uploaded: 0,
        processed: 0,
        failed: 0
    });

    try {
        const batchResponse = await fetch(apiConfig.images.createBatch, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                total_files: files.length,
                metadata: {
                    upload_timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent
                }
            })
        });

        if (!batchResponse.ok) {
            const errorText = await batchResponse.text();
            throw new Error(`Failed to create batch: ${batchResponse.statusText} - ${errorText}`);
        }

        const { batch_id } = await batchResponse.json();
        console.log('Created batch with ID:', batch_id);
        setBatchId(batch_id);

        setupWebSocket(batch_id);
        await uploadInChunks(batch_id);
        setUploadComplete(true);

    } catch (error) {
        console.error('Upload failed:', error);
        if (error instanceof Error) {
          alert(`Upload failed: ${error.message}`);
        } else {
          alert('Upload failed: An unknown error occurred.');
        }
        setIsUploading(false);
    }
  };

  const setupWebSocket = (batchId: string) => {
    console.log('WebSocket functionality disabled - configure Django Channels for real-time updates');
    return;
  };

  const uploadInChunks = async (batchId: string) => {
    const chunkSize = 10;
    
    for (let i = 0; i < files.length; i += chunkSize) {
      const chunk = files.slice(i, i + chunkSize);
      await Promise.all(chunk.map(file => uploadFile(file, batchId)));
      
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    setIsUploading(false);
  };

  const uploadFile = async (fileToUpload: UploadFile, batchId: string) => {
    const authToken = getAuthToken();
    if (!authToken) {
        throw new Error('No authentication token available');
    }

    if (!batchId) {
        throw new Error('No batch ID available');
    }

    const formData = new FormData();
    formData.append('file', fileToUpload.file);
    formData.append('batch_id', batchId);
    formData.append('file_id', fileToUpload.id);

    try {
      updateFileStatus(fileToUpload.id, 'uploading', 0);

      const response = await fetch(apiConfig.images.upload, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        },
        body: formData
      });

      if (response.ok) {
        updateFileStatus(fileToUpload.id, 'completed', 100);
        setUploadProgress(prev => ({
          ...prev,
          uploaded: prev.uploaded + 1,
          processed: prev.processed + 1 // Mark as processed since we're not auto-processing
        }));
      } else {
        const errorText = await response.text();
        throw new Error(`Upload failed: ${response.statusText} - ${errorText}`);
      }
    } catch (error: any) {
      console.error('Upload error for file:', fileToUpload.file.name, error);
      updateFileStatus(fileToUpload.id, 'error', 0, error.message);
      setUploadProgress(prev => ({
        ...prev,
        failed: prev.failed + 1
      }));
    }
  };

  const updateFileStatus = (id: string, status: UploadFile['status'], progress: number, error?: string) => {
    setFiles(prev => prev.map(f => 
      f.id === id ? { ...f, status, progress, error } : f
    ));
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending': return <Pending color="action" />;
      case 'uploading': case 'processing': return <Upload color="primary" />;
      case 'completed': return <CheckCircle color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <Pending color="action" />;
    }
  };

  const getStatusColor = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending': return 'default';
      case 'uploading': return 'info';
      case 'processing': return 'warning';
      case 'completed': return 'success';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: '100%' }}>
      <Typography variant="h4" gutterBottom>
        Bulk Image Upload
      </Typography>
      
      {uploadComplete && batchId && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Upload complete! 
          <Link href="/batch-processor" sx={{ ml: 1 }}>
            Go to Batch Processor to start YOLO processing
          </Link>
        </Alert>
      )}
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed #ccc',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'background.paper',
              '&:hover': { bgcolor: 'action.hover' }
            }}
          >
            <input {...getInputProps()} />
            <Upload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop images here...' : 'Drag & drop images or click to select'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supports PNG, JPG, JPEG, GIF, BMP, WebP (Max: 5000 files)
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {files.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upload Progress
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Chip label={`Total: ${uploadProgress.total}`} />
              <Chip label={`Uploaded: ${uploadProgress.uploaded}`} color="info" />
              <Chip label={`Processed: ${uploadProgress.processed}`} color="success" />
              <Chip label={`Failed: ${uploadProgress.failed}`} color="error" />
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={(uploadProgress.uploaded / uploadProgress.total) * 100} 
              sx={{ height: 8, borderRadius: 1 }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {Math.round((uploadProgress.uploaded / uploadProgress.total) * 100)}% Uploaded
            </Typography>
          </CardContent>
        </Card>
      )}

      {files.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Files ({files.length})
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  onClick={startUpload}
                  disabled={isUploading}
                  startIcon={<Upload />}
                >
                  {isUploading ? 'Uploading...' : 'Start Upload'}
                </Button>
                {uploadComplete && (
                  <Button
                    variant="outlined"
                    startIcon={<PlayArrow />}
                    href="/batch-processor"
                    component="a"
                  >
                    Process with YOLO
                  </Button>
                )}
                <Button
                  variant="outlined"
                  onClick={() => setFiles([])}
                  disabled={isUploading}
                >
                  Clear All
                </Button>
              </Box>
            </Box>

            <List sx={{ maxHeight: 400, overflow: 'auto' }}>
              {files.map((file) => (
                <ListItem key={file.id} divider>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    {getStatusIcon(file.status)}
                    <ListItemText
                      primary={file.file.name}
                      secondary={
                        <React.Fragment>
                          <Typography variant="caption" display="block" component="span">
                            Size: {(file.file.size / 1024 / 1024).toFixed(2)} MB
                          </Typography>
                          {file.status !== 'pending' && (
                            <LinearProgress
                              variant="determinate"
                              value={file.progress}
                              sx={{ mt: 1, height: 4 }}
                            />
                          )}
                          {file.error && (
                            <Typography variant="caption" color="error" display="block" component="span" sx={{ mt: 1 }}>
                              {file.error}
                            </Typography>
                          )}
                        </React.Fragment>
                      }
                      sx={{ ml: 2, flex: 1 }}
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={file.status}
                        color={getStatusColor(file.status)}
                        size="small"
                      />
                      <IconButton
                        onClick={() => removeFile(file.id)}
                        disabled={isUploading}
                        size="small"
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </Box>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default BulkImageUpload;