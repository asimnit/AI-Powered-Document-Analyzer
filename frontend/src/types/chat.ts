/**
 * Chat Type Definitions
 * 
 * TypeScript interfaces for conversations, messages, and chat-related data structures
 */

// ==================== Source Citation ====================

export interface SourceCitation {
  store_id: number;
  store_name: string;
  document_id: number;
  document_name: string;
  chunk_id: number;
  chunk_text: string;
  page_number: number | null;
  similarity_score: number;
}

// ==================== Message ====================

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  sources: SourceCitation[] | null;
  token_count: number | null;
  created_at: string;
}

// ==================== Conversation ====================

export interface Conversation {
  id: number;
  user_id: number;
  title: string | null;
  store_count: number;
  message_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface AttachedStoreInfo {
  store_id: number;
  store_name: string;
  document_count: number;
  attached_at: string;
}

export interface ConversationDetail {
  id: number;
  user_id: number;
  title: string | null;
  attached_stores: AttachedStoreInfo[];
  messages: Message[];
  created_at: string;
  updated_at: string | null;
}

// ==================== Requests ====================

export interface CreateConversationRequest {
  title?: string;
  store_ids?: number[];
}

export interface UpdateConversationRequest {
  title: string;
}

export interface AttachStoresRequest {
  store_ids: number[];
}

export interface AskQuestionRequest {
  query: string;
}

// ==================== Responses ====================

export interface AskQuestionResponse {
  user_message: Message;
  assistant_message: Message;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export interface AttachStoresResponse {
  conversation_id: number;
  attached_stores: AttachedStoreInfo[];
  total_stores: number;
}

export interface DetachStoreResponse {
  conversation_id: number;
  detached_store_id: number;
  remaining_stores: number;
}
