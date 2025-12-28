/**
 * Store Service
 * 
 * API functions for document store management
 */

import api from './api';
import type {
  DocumentStore,
  StoreDetail,
  StoreListResponse,
  CreateStoreData,
  UpdateStoreData,
  StoreDeleteResponse,
  ProcessAllResponse,
  RetryAllFailedResponse,
  RetryAllIndexingResponse,
  SearchRequest,
  SearchResponse
} from '../types/store';
import type { DocumentListResponse, ProcessingStatus } from '../types/document';

/**
 * Get all stores for current user
 */
export const getAllStores = async (
  page: number = 1,
  pageSize: number = 20
): Promise<StoreListResponse> => {
  const response = await api.get<StoreListResponse>('/api/v1/stores/', {
    params: { page, page_size: pageSize }
  });
  return response.data;
};

/**
 * Get store details with statistics
 */
export const getStore = async (id: number): Promise<StoreDetail> => {
  const response = await api.get<StoreDetail>(`/api/v1/stores/${id}`);
  return response.data;
};

/**
 * Create a new store
 */
export const createStore = async (data: CreateStoreData): Promise<DocumentStore> => {
  const response = await api.post<DocumentStore>('/api/v1/stores/', data);
  return response.data;
};

/**
 * Update store information
 */
export const updateStore = async (id: number, data: UpdateStoreData): Promise<DocumentStore> => {
  const response = await api.put<DocumentStore>(`/api/v1/stores/${id}`, data);
  return response.data;
};

/**
 * Delete store and all documents
 */
export const deleteStore = async (id: number): Promise<StoreDeleteResponse> => {
  const response = await api.delete<StoreDeleteResponse>(`/api/v1/stores/${id}`);
  return response.data;
};

/**
 * Get documents in a store
 */
export const getStoreDocuments = async (
  storeId: number,
  page: number = 1,
  pageSize: number = 20,
  status?: ProcessingStatus,
  search?: string
): Promise<DocumentListResponse> => {
  const params: any = {
    page,
    page_size: pageSize,
  };

  if (status) {
    params.status_filter = status;
  }

  if (search) {
    params.search = search;
  }

  const response = await api.get<DocumentListResponse>(
    `/api/v1/stores/${storeId}/documents`,
    { params }
  );
  return response.data;
};

/**
 * Process all COMPLETED documents in store
 */
export const processAllDocuments = async (storeId: number): Promise<ProcessAllResponse> => {
  const response = await api.post<ProcessAllResponse>(
    `/api/v1/stores/${storeId}/process-all`
  );
  return response.data;
};

/**
 * Retry all failed documents in store
 */
export const retryAllFailed = async (storeId: number): Promise<RetryAllFailedResponse> => {
  const response = await api.post<RetryAllFailedResponse>(
    `/api/v1/stores/${storeId}/retry-all-failed`
  );
  return response.data;
};

/**
 * Retry indexing for all completed documents in store
 */
export const retryAllIndexing = async (storeId: number): Promise<RetryAllIndexingResponse> => {
  const response = await api.post<RetryAllIndexingResponse>(
    `/api/v1/stores/${storeId}/retry-all-indexing`
  );
  return response.data;
};

/**
 * Move document to another store
 */
export const moveDocument = async (documentId: number, targetStoreId: number): Promise<void> => {
  await api.patch(`/api/v1/documents/${documentId}/move`, {
    store_id: targetStoreId
  });
};

/**
 * Search within a store using semantic search
 */
export const searchInStore = async (
  storeId: number,
  query: string,
  topK: number = 5
): Promise<SearchResponse> => {
  const response = await api.post<SearchResponse>(
    `/api/v1/stores/${storeId}/search`,
    { query, top_k: topK }
  );
  return response.data;
};

export default {
  getAllStores,
  getStore,
  createStore,
  updateStore,
  deleteStore,
  getStoreDocuments,
  processAllDocuments,
  retryAllFailed,
  retryAllIndexing,
  moveDocument,
  searchInStore
};
