/**
 * Document Store Types
 * 
 * TypeScript interfaces for document stores matching backend schemas
 */

export interface DocumentStore {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  document_count: number;
  created_at: string;
  updated_at?: string;
}

export interface StoreStatusBreakdown {
  uploaded: number;
  processing: number;
  completed: number;
  indexing: number;
  indexed: number;
  partially_indexed: number;
  indexing_failed: number;
  failed: number;
}

export interface StoreDetail extends DocumentStore {
  status_breakdown: StoreStatusBreakdown;
  total_size: number; // in bytes
}

export interface StoreListResponse {
  stores: DocumentStore[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateStoreData {
  name: string;
  description?: string;
}

export interface UpdateStoreData {
  name?: string;
  description?: string;
}

export interface StoreDeleteResponse {
  message: string;
  deleted_documents_count: number;
}

export interface ProcessAllResponse {
  message: string;
  task_ids: string[];
  documents_queued: number;
}

export interface RetryAllFailedResponse {
  message: string;
  task_ids: string[];
  documents_queued: number;
}

export interface RetryAllIndexingResponse {
  message: string;
  task_ids: string[];
  documents_queued: number;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
}

export interface SearchResultItem {
  chunk_id: number;
  chunk_content: string;
  chunk_index: number;
  document_id: number;
  document_filename: string;
  similarity_score: number;
  page_numbers: number[];
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total_results: number;
  store_id: number;
}
