/**
 * Document Types
 * 
 * TypeScript interfaces matching backend Pydantic schemas
 */

export type ProcessingStatus = "uploaded" | "processing" | "completed" | "failed";

export const ProcessingStatus = {
  UPLOADED: "uploaded" as const,
  PROCESSING: "processing" as const,
  COMPLETED: "completed" as const,
  FAILED: "failed" as const,
};

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  s3_path: string;
  processing_status: ProcessingStatus;
  upload_date: string;  // Changed from uploaded_at to upload_date
  processed_at?: string;
  error_message?: string;
  user_id: number;
  // Computed properties
  file_size_mb: number;
  is_ready_for_query: boolean;
}

export interface DocumentUploadResponse {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  file_size_mb: number;
  processing_status: ProcessingStatus;
  upload_date: string;  // Changed from uploaded_at to upload_date
  message: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DocumentStats {
  total_documents: number;
  total_size_bytes: number;
  total_size_mb: number;
  by_status: {
    uploaded: number;
    processing: number;
    completed: number;
    failed: number;
  };
  by_type: Record<string, number>;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}
