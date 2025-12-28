/**
 * Document Service
 * 
 * API functions for document management
 */

import api from './api';
import type { 
  Document, 
  DocumentUploadResponse, 
  DocumentListResponse, 
  DocumentStats,
  ProcessingStatus 
} from '../types/document';

/**
 * Upload a document file
 */
export const uploadDocument = async (
  file: File,
  onProgress?: (percentage: number) => void,
  storeId?: number
): Promise<DocumentUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const url = storeId 
    ? `/api/v1/documents/upload?store_id=${storeId}`
    : '/api/v1/documents/upload';

  const response = await api.post<DocumentUploadResponse>(
    url,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentage = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentage);
        }
      },
    }
  );

  return response.data;
};

/**
 * Get paginated list of documents
 */
export const getDocuments = async (
  page: number = 1,
  pageSize: number = 10,
  status?: ProcessingStatus
): Promise<DocumentListResponse> => {
  const params: any = {
    page,
    page_size: pageSize,
  };

  if (status) {
    params.status_filter = status;  // Changed from 'status' to 'status_filter'
  }

  const response = await api.get<DocumentListResponse>('/api/v1/documents/', { params });
  return response.data;
};

/**
 * Get single document by ID
 */
export const getDocument = async (id: number): Promise<Document> => {
  const response = await api.get<Document>(`/api/v1/documents/${id}`);
  return response.data;
};

/**
 * Delete a document
 */
export const deleteDocument = async (id: number): Promise<{ message: string }> => {
  const response = await api.delete<{ message: string }>(`/api/v1/documents/${id}`);
  return response.data;
};

/**
 * Download a document
 */
export const downloadDocument = async (id: number, filename: string): Promise<void> => {
  const response = await api.get(`/api/v1/documents/download/${id}`, {
    responseType: 'blob',
  });

  // Create a download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Get document statistics
 */
export const getDocumentStats = async (): Promise<DocumentStats> => {
  const response = await api.get<DocumentStats>('/api/v1/documents/stats/overview');
  return response.data;
};

/**
 * Trigger document processing
 */
export const processDocument = async (id: number): Promise<{ message: string; task_id: string; status: string }> => {
  const response = await api.post<{ message: string; task_id: string; status: string }>(`/api/v1/documents/${id}/process`);
  return response.data;
};

/**
 * Retry document indexing (embedding generation)
 */
export const retryIndexing = async (id: number): Promise<{ message: string; task_id: string; status: string }> => {
  const response = await api.post<{ message: string; task_id: string; status: string }>(`/api/v1/documents/${id}/retry-indexing`);
  return response.data;
};

const documentService = {
  uploadDocument,
  getDocuments,
  getDocument,
  deleteDocument,
  downloadDocument,
  getDocumentStats,
  processDocument,
  retryIndexing,
};

export default documentService;
