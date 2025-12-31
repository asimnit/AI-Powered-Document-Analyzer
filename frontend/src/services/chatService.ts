/**
 * Chat Service
 * 
 * API client for chat/conversation endpoints
 */

import axios from 'axios';
import type {
  Conversation,
  ConversationDetail,
  ConversationListResponse,
  CreateConversationRequest,
  UpdateConversationRequest,
  AttachStoresRequest,
  AttachStoresResponse,
  DetachStoreResponse,
  AskQuestionRequest,
  AskQuestionResponse,
  AttachedStoreInfo,
} from '../types/chat';

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ChatService {
  /**
   * Get all conversations for the current user
   */
  async getConversations(): Promise<ConversationListResponse> {
    const response = await axios.get<ConversationListResponse>(
      `${API_BASE_URL}/conversations`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Create a new conversation
   */
  async createConversation(data: CreateConversationRequest): Promise<Conversation> {
    const response = await axios.post<Conversation>(
      `${API_BASE_URL}/conversations`,
      data,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  }

  /**
   * Get conversation details with messages and attached stores
   */
  async getConversation(conversationId: number): Promise<ConversationDetail> {
    const response = await axios.get<ConversationDetail>(
      `${API_BASE_URL}/conversations/${conversationId}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Update conversation title
   */
  async updateConversation(
    conversationId: number,
    data: UpdateConversationRequest
  ): Promise<Conversation> {
    const response = await axios.put<Conversation>(
      `${API_BASE_URL}/conversations/${conversationId}`,
      data,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  }

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: number): Promise<void> {
    await axios.delete(`${API_BASE_URL}/conversations/${conversationId}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
  }

  /**
   * Get attached stores for a conversation
   */
  async getAttachedStores(conversationId: number): Promise<AttachedStoreInfo[]> {
    const detail = await this.getConversation(conversationId);
    return detail.attached_stores || [];
  }

  /**
   * Attach stores to a conversation
   */
  async attachStores(
    conversationId: number,
    data: AttachStoresRequest
  ): Promise<AttachStoresResponse> {
    const response = await axios.post<AttachStoresResponse>(
      `${API_BASE_URL}/conversations/${conversationId}/stores`,
      data,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  }

  /**
   * Detach a store from a conversation
   */
  async detachStore(
    conversationId: number,
    storeId: number
  ): Promise<DetachStoreResponse> {
    const response = await axios.delete<DetachStoreResponse>(
      `${API_BASE_URL}/conversations/${conversationId}/stores/${storeId}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Ask a question in a conversation (RAG-powered Q&A)
   */
  async askQuestion(
    conversationId: number,
    data: AskQuestionRequest
  ): Promise<AskQuestionResponse> {
    const response = await axios.post<AskQuestionResponse>(
      `${API_BASE_URL}/conversations/${conversationId}/ask`,
      data,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  }
}

export default new ChatService();
