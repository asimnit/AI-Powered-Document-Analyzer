/**
 * Chat Store (Zustand)
 * 
 * Global state management for chat/conversations
 */

import { create } from 'zustand';
import chatService from '../services/chatService';
import type {
  Conversation,
  ConversationDetail,
  Message,
  AttachedStoreInfo,
  CreateConversationRequest,
} from '../types/chat';

interface ChatStore {
  // State
  conversations: Conversation[];
  currentConversation: ConversationDetail | null;
  messages: Message[];
  attachedStores: AttachedStoreInfo[];
  loading: boolean;
  error: string | null;
  askingQuestion: boolean;

  // Actions - Conversations
  fetchConversations: () => Promise<void>;
  createConversation: (data: CreateConversationRequest) => Promise<Conversation>;
  selectConversation: (conversationId: number) => Promise<void>;
  updateConversationTitle: (conversationId: number, title: string) => Promise<void>;
  deleteConversation: (conversationId: number) => Promise<void>;
  clearCurrentConversation: () => void;
  
  // Actions - Messages & Stores
  fetchMessages: (conversationId: number) => Promise<void>;
  fetchAttachedStores: (conversationId: number) => Promise<void>;

  // Actions - Store Management
  attachStores: (conversationId: number, storeIds: number[]) => Promise<void>;
  detachStore: (conversationId: number, storeId: number) => Promise<void>;

  // Actions - Chat
  askQuestion: (conversationId: number, query: string) => Promise<void>;

  // Helpers
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  // Initial State
  conversations: [],
  currentConversation: null,
  messages: [],
  attachedStores: [],
  loading: false,
  error: null,
  askingQuestion: false,

  // ==================== Conversation Actions ====================

  fetchConversations: async () => {
    set({ loading: true, error: null });
    try {
      const response = await chatService.getConversations();
      set({ conversations: response.conversations, loading: false });
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch conversations';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  createConversation: async (data: CreateConversationRequest) => {
    set({ loading: true, error: null });
    try {
      const newConversation = await chatService.createConversation(data);
      set((state) => ({
        conversations: [newConversation, ...state.conversations],
        loading: false,
      }));
      return newConversation;
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to create conversation';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  selectConversation: async (conversationId: number) => {
    set({ loading: true, error: null });
    try {
      const conversation = await chatService.getConversation(conversationId);
      set({
        currentConversation: conversation,
        messages: conversation.messages,
        attachedStores: conversation.attached_stores,
        loading: false,
      });
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to load conversation';
      set({ error: errorMsg, loading: false });
      throw error;
    }
  },

  updateConversationTitle: async (conversationId: number, title: string) => {
    set({ error: null });
    try {
      await chatService.updateConversation(conversationId, { title });
      
      // Update in conversations list
      set((state) => ({
        conversations: state.conversations.map((conv) =>
          conv.id === conversationId ? { ...conv, title } : conv
        ),
      }));

      // Update current conversation if it's the one being updated
      if (get().currentConversation?.id === conversationId) {
        set((state) => ({
          currentConversation: state.currentConversation
            ? { ...state.currentConversation, title }
            : null,
        }));
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to update title';
      set({ error: errorMsg });
      throw error;
    }
  },

  deleteConversation: async (conversationId: number) => {
    set({ error: null });
    try {
      await chatService.deleteConversation(conversationId);
      
      set((state) => ({
        conversations: state.conversations.filter((conv) => conv.id !== conversationId),
        currentConversation:
          state.currentConversation?.id === conversationId
            ? null
            : state.currentConversation,
        messages: state.currentConversation?.id === conversationId ? [] : state.messages,
        attachedStores:
          state.currentConversation?.id === conversationId ? [] : state.attachedStores,
      }));
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to delete conversation';
      set({ error: errorMsg });
      throw error;
    }
  },

  clearCurrentConversation: () => {
    set({
      currentConversation: null,
      messages: [],
      attachedStores: [],
    });
  },  
  // ==================== Message & Store Fetching ====================

  fetchMessages: async (conversationId: number) => {
    set({ error: null });
    try {
      const detail = await chatService.getConversation(conversationId);
      set({ messages: detail.messages || [] });
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch messages';
      set({ error: errorMsg });
      throw error;
    }
  },

  fetchAttachedStores: async (conversationId: number) => {
    set({ error: null });
    try {
      const stores = await chatService.getAttachedStores(conversationId);
      set({ attachedStores: stores });
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch attached stores';
      set({ error: errorMsg });
      throw error;
    }
  },
  // ==================== Store Management Actions ====================

  attachStores: async (conversationId: number, storeIds: number[]) => {
    set({ error: null });
    try {
      const response = await chatService.attachStores(conversationId, { store_ids: storeIds });
      
      // Update current conversation if it's the active one
      if (get().currentConversation?.id === conversationId) {
        set({ attachedStores: response.attached_stores });
        
        // Also update the store_count in currentConversation
        set((state) => ({
          currentConversation: state.currentConversation
            ? { ...state.currentConversation, attached_stores: response.attached_stores }
            : null,
        }));
      }

      // Update in conversations list
      set((state) => ({
        conversations: state.conversations.map((conv) =>
          conv.id === conversationId
            ? { ...conv, store_count: response.total_stores }
            : conv
        ),
      }));
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to attach stores';
      set({ error: errorMsg });
      throw error;
    }
  },

  detachStore: async (conversationId: number, storeId: number) => {
    set({ error: null });
    try {
      const response = await chatService.detachStore(conversationId, storeId);
      
      // Update current conversation if it's the active one
      if (get().currentConversation?.id === conversationId) {
        set((state) => ({
          attachedStores: state.attachedStores.filter((s) => s.store_id !== storeId),
        }));
        
        // Update store count
        set((state) => ({
          currentConversation: state.currentConversation
            ? {
                ...state.currentConversation,
                attached_stores: state.attachedStores.filter((s) => s.store_id !== storeId),
              }
            : null,
        }));
      }

      // Update in conversations list
      set((state) => ({
        conversations: state.conversations.map((conv) =>
          conv.id === conversationId
            ? { ...conv, store_count: response.remaining_stores }
            : conv
        ),
      }));
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to detach store';
      set({ error: errorMsg });
      throw error;
    }
  },

  // ==================== Chat Actions ====================

  askQuestion: async (conversationId: number, query: string) => {
    set({ askingQuestion: true, error: null });
    try {
      const response = await chatService.askQuestion(conversationId, { query });
      
      // Debug: Log the response to see what we're getting
      console.log('📥 Ask Question Response:', {
        user_message: response.user_message,
        assistant_message: response.assistant_message,
        assistant_content: response.assistant_message?.content,
        assistant_sources: response.assistant_message?.sources
      });
      
      // Add both user and assistant messages to the list
      set((state) => ({
        messages: [...state.messages, response.user_message, response.assistant_message],
        askingQuestion: false,
      }));

      // Update message count in conversations list
      set((state) => ({
        conversations: state.conversations.map((conv) =>
          conv.id === conversationId
            ? { ...conv, message_count: conv.message_count + 2 }
            : conv
        ),
      }));

      // Update current conversation if it's the active one
      if (get().currentConversation?.id === conversationId) {
        set((state) => ({
          currentConversation: state.currentConversation
            ? {
                ...state.currentConversation,
                messages: [...state.messages],
                title:
                  state.currentConversation.title ||
                  query.substring(0, 60) + (query.length > 60 ? '...' : ''),
              }
            : null,
        }));
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to get response';
      set({ error: errorMsg, askingQuestion: false });
      throw error;
    }
  },

  // ==================== Helper Actions ====================

  setError: (error: string | null) => set({ error }),
  
  clearError: () => set({ error: null }),
}));
