import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  CircularProgress,
  Switch,
  FormControlLabel,
  IconButton
} from '@mui/material';
import {
  PlayArrow,
  Refresh,
  Info,
  CheckCircle,
  Error as ErrorIcon,
  Pending,
  Visibility,
  Delete
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { apiConfig } from '../../config/api';

interface BatchInfo {
  id: string;
  total_files: number;
  uploaded_files: number;
  processed_files: number;
  failed_files: number;
  status: string;
  progress_percent: number;
  created_at: string;
  completed_at?: string;
  metadata?: any;
}

interface YoloModelInfo {
  model_info: {
    name: string;
    version: string;
    keypoint_count: number;
    input_size: [number, number];
    confidence_threshold: number;
    model_type: string;
  };
  model_path: string;
  model_exists: boolean;
  confidence_threshold: number;
  processing_enabled: boolean;
}

const BatchProcessor: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [batches, setBatches] = useState<BatchInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingBatches, setProcessingBatches] = useState<Set<string>>(new Set());
  const [deletingBatches, setDeletingBatches] = useState<Set<string>>(new Set());
  const [modelInfo, setModelInfo] = useState<YoloModelInfo | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<BatchInfo | null>(null);
  const [showModelInfo, setShowModelInfo] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [batchToDelete, setBatchToDelete] = useState<BatchInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Polling controls
  const [isPollingActive, setIsPollingActive] = useState(false);
  const [pollingInterval, setPollingInterval] = useState(5000); // 5 seconds default
  const pollingIntervalRef = useRef<number | null>(null);
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null);

  useEffect(() => {
    // Initial load
    fetchBatches();
    fetchModelInfo();
  }, []);

  // Separate effect for managing polling
  useEffect(() => {
    if (isPollingActive) {
      startPolling();
    } else {
      stopPolling();
    }
    
    return () => stopPolling(); // Cleanup on unmount
  }, [isPollingActive, pollingInterval]);

  const startPolling = () => {
    stopPolling(); // Clear any existing interval
    pollingIntervalRef.current = setInterval(() => {
      fetchBatches();
    }, pollingInterval);
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const togglePolling = () => {
    setIsPollingActive(!isPollingActive);
  };

  const getAuthToken = () => {
    if (!isAuthenticated || !user?.accessToken) {
      return null;
    }
    return user.accessToken;
  };

  const fetchBatches = async () => {
    const token = getAuthToken();
    if (!token) return;

    try {
      const response = await fetch(apiConfig.images.batches, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setBatches(data.batches || []);
        setError(null);
        setLastRefreshTime(new Date());
      } else {
        console.error('Failed to fetch batches');
      }
    } catch (error) {
      console.error('Error fetching batches:', error);
      setError('Failed to load batches');
    } finally {
      setLoading(false);
    }
  };

  const manualRefresh = async () => {
    setLoading(true);
    await fetchBatches();
  };

  const fetchModelInfo = async () => {
    const token = getAuthToken();
    if (!token) return;

    try {
      const response = await fetch(apiConfig.images.yoloModelInfo, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setModelInfo(data);
      }
    } catch (error) {
      console.error('Error fetching model info:', error);
    }
  };

  const processBatch = async (batchId: string) => {
    const token = getAuthToken();
    if (!token) return;

    setProcessingBatches(prev => new Set(prev).add(batchId));

    try {
      const response = await fetch(apiConfig.images.batchProcess(batchId), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Processing started:', result);
        // Refresh batches to show updated status
        fetchBatches();
      } else {
        const errorData = await response.json();
        setError(`Failed to start processing: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error starting batch processing:', error);
      setError('Failed to start batch processing');
    } finally {
      setProcessingBatches(prev => {
        const newSet = new Set(prev);
        newSet.delete(batchId);
        return newSet;
      });
    }
  };

  const retryFailedImages = async (batchId: string) => {
    const token = getAuthToken();
    if (!token) return;

    try {
      const response = await fetch(apiConfig.images.batchRetry(batchId), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Retry started:', result);
        fetchBatches();
      } else {
        const errorData = await response.json();
        setError(`Failed to retry processing: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error retrying batch:', error);
      setError('Failed to retry batch processing');
    }
  };

  const deleteBatch = async (batchId: string) => {
    const token = getAuthToken();
    if (!token) return;

    setDeletingBatches(prev => new Set(prev).add(batchId));

    try {
      const response = await fetch(apiConfig.images.batchDelete(batchId), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Batch deleted:', result);
        // Remove the batch from the list
        setBatches(prev => prev.filter(batch => batch.id !== batchId));
        setError(null);
      } else {
        const errorData = await response.json();
        setError(`Failed to delete batch: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error deleting batch:', error);
      setError('Failed to delete batch');
    } finally {
      setDeletingBatches(prev => {
        const newSet = new Set(prev);
        newSet.delete(batchId);
        return newSet;
      });
      setDeleteDialogOpen(false);
      setBatchToDelete(null);
    }
  };

  const handleDeleteClick = (batch: BatchInfo) => {
    setBatchToDelete(batch);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (batchToDelete) {
      deleteBatch(batchToDelete.id);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
      case 'uploading':
        return <Pending color="action" />;
      case 'processing':
        // Use CircularProgress for processing status
        return <CircularProgress size={20} color="primary" />;
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
      case 'cancelled':
        return <ErrorIcon color="error" />;
      default:
        return <Pending color="action" />;
    }
  };

  const getStatusColor = (status: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (status.toLowerCase()) {
      case 'pending': return 'default';
      case 'uploading': return 'info';
      case 'processing': return 'warning';
      case 'completed': return 'success';
      case 'failed':
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const canProcess = (batch: BatchInfo) => {
    return ['uploading', 'completed', 'failed'].includes(batch.status.toLowerCase()) && 
           batch.uploaded_files > 0;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          YOLO Batch Processor
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<Info />}
            onClick={() => setShowModelInfo(true)}
          >
            Model Info
          </Button>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={16} /> : <Refresh />}
            onClick={manualRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Polling Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Auto-Refresh Controls
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={isPollingActive}
                  onChange={togglePolling}
                  color="primary"
                />
              }
              label={isPollingActive ? "Auto-refresh ON" : "Auto-refresh OFF"}
            />
            {isPollingActive && (
              <Chip
                icon={<CircularProgress size={16} />}
                label={`Refreshing every ${pollingInterval / 1000}s`}
                color="primary"
                variant="outlined"
              />
            )}
            {lastRefreshTime && (
              <Typography variant="body2" color="text.secondary">
                Last updated: {lastRefreshTime.toLocaleTimeString()}
              </Typography>
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            <Button
              size="small"
              variant={pollingInterval === 3000 ? "contained" : "outlined"}
              onClick={() => setPollingInterval(3000)}
            >
              3s
            </Button>
            <Button
              size="small"
              variant={pollingInterval === 5000 ? "contained" : "outlined"}
              onClick={() => setPollingInterval(5000)}
            >
              5s
            </Button>
            <Button
              size="small"
              variant={pollingInterval === 10000 ? "contained" : "outlined"}
              onClick={() => setPollingInterval(10000)}
            >
              10s
            </Button>
            <Button
              size="small"
              variant={pollingInterval === 30000 ? "contained" : "outlined"}
              onClick={() => setPollingInterval(30000)}
            >
              30s
            </Button>
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {modelInfo && !modelInfo.model_exists && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          YOLO model file not found at: {modelInfo.model_path}
        </Alert>
      )}

      {!modelInfo?.processing_enabled && (
        <Alert severity="info" sx={{ mb: 2 }}>
          YOLO processing is currently disabled in settings.
        </Alert>
      )}

      {batches.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" color="text.secondary">
              No upload batches found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Upload some images first to see batches here.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {batches.map((batch) => (
            <Grid item xs={12} md={6} key={batch.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Batch {batch.id.substring(0, 8)}...
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Created: {formatDate(batch.created_at)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        icon={getStatusIcon(batch.status)}
                        label={batch.status}
                        color={getStatusColor(batch.status)}
                        size="small"
                      />
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteClick(batch)}
                        disabled={deletingBatches.has(batch.id)}
                        title="Delete batch"
                      >
                        {deletingBatches.has(batch.id) ? (
                          <CircularProgress size={16} />
                        ) : (
                          <Delete />
                        )}
                      </IconButton>
                    </Box>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2">
                          <strong>Total:</strong> {batch.total_files}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Uploaded:</strong> {batch.uploaded_files}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2">
                          <strong>Processed:</strong> {batch.processed_files}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Failed:</strong> {batch.failed_files}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={batch.progress_percent}
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      {Math.round(batch.progress_percent)}% Complete
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={processingBatches.has(batch.id) ? <CircularProgress size={16} /> : <PlayArrow />}
                      onClick={() => processBatch(batch.id)}
                      disabled={!canProcess(batch) || processingBatches.has(batch.id) || !modelInfo?.processing_enabled}
                    >
                      {processingBatches.has(batch.id) ? 'Processing...' : 'Process with YOLO'}
                    </Button>
                    
                    {batch.failed_files > 0 && (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<Refresh />}
                        onClick={() => retryFailedImages(batch.id)}
                      >
                        Retry Failed ({batch.failed_files})
                      </Button>
                    )}
                    
                    <Button
                      variant="text"
                      size="small"
                      startIcon={<Visibility />}
                      onClick={() => setSelectedBatch(batch)}
                    >
                      View Details
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Model Info Dialog */}
      <Dialog open={showModelInfo} onClose={() => setShowModelInfo(false)} maxWidth="md" fullWidth>
        <DialogTitle>YOLO Model Information</DialogTitle>
        <DialogContent>
          {modelInfo ? (
            <Box>
              <Typography variant="h6" gutterBottom>Model Details</Typography>
              <List>
                <ListItem>
                  <ListItemText primary="Name" secondary={modelInfo.model_info?.name || 'N/A'} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Version" secondary={modelInfo.model_info?.version || 'N/A'} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Keypoints" secondary={`${modelInfo.model_info?.keypoint_count || 0} keypoints`} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Model Type" secondary={modelInfo.model_info?.model_type || 'N/A'} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Input Size" secondary={`${modelInfo.model_info?.input_size?.[0] || 0} x ${modelInfo.model_info?.input_size?.[1] || 0}`} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Confidence Threshold" secondary={modelInfo.confidence_threshold} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Model File" secondary={modelInfo.model_path} />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Model Status" 
                    secondary={
                      <Chip
                        label={modelInfo.model_exists ? 'Available' : 'Not Found'}
                        color={modelInfo.model_exists ? 'success' : 'error'}
                        size="small"
                      />
                    }
                  />
                </ListItem>
              </List>
            </Box>
          ) : (
            <Typography>Loading model information...</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowModelInfo(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Batch Details Dialog */}
      <Dialog open={!!selectedBatch} onClose={() => setSelectedBatch(null)} maxWidth="md" fullWidth>
        <DialogTitle>Batch Details</DialogTitle>
        <DialogContent>
          {selectedBatch && (
            <Box>
              <Typography variant="h6" gutterBottom>Batch {selectedBatch.id}</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography><strong>Status:</strong> {selectedBatch.status}</Typography>
                  <Typography><strong>Total Files:</strong> {selectedBatch.total_files}</Typography>
                  <Typography><strong>Uploaded:</strong> {selectedBatch.uploaded_files}</Typography>
                  <Typography><strong>Processed:</strong> {selectedBatch.processed_files}</Typography>
                  <Typography><strong>Failed:</strong> {selectedBatch.failed_files}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography><strong>Created:</strong> {formatDate(selectedBatch.created_at)}</Typography>
                  {selectedBatch.completed_at && (
                    <Typography><strong>Completed:</strong> {formatDate(selectedBatch.completed_at)}</Typography>
                  )}
                  <Typography><strong>Progress:</strong> {Math.round(selectedBatch.progress_percent)}%</Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedBatch(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">Delete Batch</DialogTitle>
        <DialogContent>
          <Typography id="delete-dialog-description">
            Are you sure you want to delete batch "{batchToDelete?.id.substring(0, 8)}..."? 
            This action cannot be undone and will permanently remove:
            <br />• {batchToDelete?.uploaded_files || 0} uploaded images
            <br />• {batchToDelete?.processed_files || 0} processed results
            <br />• All associated annotations and metadata
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} color="primary">
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deletingBatches.has(batchToDelete?.id || '')}
          >
            {deletingBatches.has(batchToDelete?.id || '') ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BatchProcessor;
