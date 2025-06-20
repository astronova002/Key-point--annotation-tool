// API Configuration - centralized URL management
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws';

export const apiConfig = {
  baseURL: API_BASE_URL,
  wsURL: WS_BASE_URL,
  
  // API endpoints
  auth: {
    login: `${API_BASE_URL}/auth/login/`,
    register: `${API_BASE_URL}/auth/register/`,
    logout: `${API_BASE_URL}/auth/logout/`,
    status: `${API_BASE_URL}/auth/status/`,
    tokenRefresh: `${API_BASE_URL}/auth/token/refresh/`,
    getUsers: `${API_BASE_URL}/auth/get-users/`,
    approveUser: (userId: number) => `${API_BASE_URL}/auth/approve-user/${userId}/`,
    updateRole: (userId: number) => `${API_BASE_URL}/auth/update-role/${userId}/`,
    deleteUser: (userId: number) => `${API_BASE_URL}/auth/delete-user/${userId}/`,
  },
  
  images: {
    createBatch: `${API_BASE_URL}/images/create-batch/`,
    upload: `${API_BASE_URL}/images/upload/`,
    batches: `${API_BASE_URL}/images/batches/`,
    batchStatus: (batchId: string) => `${API_BASE_URL}/images/batch/${batchId}/status/`,
    batchImages: (batchId: string) => `${API_BASE_URL}/images/batch/${batchId}/images/`,
    batchProcess: (batchId: string) => `${API_BASE_URL}/images/batch/${batchId}/process/`,
    batchRetry: (batchId: string) => `${API_BASE_URL}/images/batch/${batchId}/retry/`,
    batchCancel: (batchId: string) => `${API_BASE_URL}/images/batch/${batchId}/cancel/`,
    batchDelete: (batchId: string) => `${API_BASE_URL}/images/batch/${batchId}/delete/`,
    processImage: (imageId: string) => `${API_BASE_URL}/images/image/${imageId}/process/`,
    yoloModelInfo: `${API_BASE_URL}/images/yolo-model-info/`,
  },
  
  websockets: {
    uploadProgress: (batchId: string) => `${WS_BASE_URL}/upload-progress/${batchId}/`,
  }
};

export default apiConfig;
