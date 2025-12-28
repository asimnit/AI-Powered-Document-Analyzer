/**
 * Store State Management (Zustand)
 * 
 * Global state for document stores
 */

import { create } from 'zustand';
import type { DocumentStore, StoreDetail, CreateStoreData, UpdateStoreData } from '../types/store';
import storeService from '../services/storeService';
import { logger } from '../utils/logger';

interface StoreState {
  stores: DocumentStore[];
  currentStore: StoreDetail | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchStores: () => Promise<void>;
  fetchStoreById: (id: number) => Promise<void>;
  createStore: (data: CreateStoreData) => Promise<DocumentStore>;
  updateStore: (id: number, data: UpdateStoreData) => Promise<DocumentStore>;
  deleteStore: (id: number) => Promise<void>;
  setCurrentStore: (store: StoreDetail | null) => void;
  clearError: () => void;
}

export const useStoreStore = create<StoreState>((set, get) => ({
  stores: [],
  currentStore: null,
  isLoading: false,
  error: null,

  /**
   * Fetch all stores for current user
   */
  fetchStores: async () => {
    logger.info('Fetching stores...');
    set({ isLoading: true, error: null });
    try {
      const response = await storeService.getAllStores();
      set({
        stores: response.stores,
        isLoading: false,
      });
      logger.info(`✅ Fetched ${response.stores.length} stores`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch stores';
      logger.error('❌ Failed to fetch stores', { error: errorMessage });
      set({
        stores: [],
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  /**
   * Fetch store details by ID
   */
  fetchStoreById: async (id: number) => {
    logger.info(`Fetching store details: ${id}`);
    set({ isLoading: true, error: null });
    try {
      const store = await storeService.getStore(id);
      set({
        currentStore: store,
        isLoading: false,
      });
      logger.info(`✅ Fetched store details: ${store.name}`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch store details';
      logger.error('❌ Failed to fetch store details', { error: errorMessage });
      set({
        currentStore: null,
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  /**
   * Create a new store
   */
  createStore: async (data: CreateStoreData) => {
    logger.info('Creating store...', { name: data.name });
    set({ isLoading: true, error: null });
    try {
      const store = await storeService.createStore(data);
      set((state) => ({
        stores: [store, ...state.stores],
        isLoading: false,
      }));
      logger.info(`✅ Created store: ${store.name}`);
      return store;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to create store';
      logger.error('❌ Failed to create store', { error: errorMessage });
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  /**
   * Update store information
   */
  updateStore: async (id: number, data: UpdateStoreData) => {
    logger.info(`Updating store: ${id}`, data);
    set({ isLoading: true, error: null });
    try {
      const updatedStore = await storeService.updateStore(id, data);
      set((state) => ({
        stores: state.stores.map((s) => (s.id === id ? updatedStore : s)),
        currentStore: state.currentStore?.id === id 
          ? { ...state.currentStore, ...updatedStore }
          : state.currentStore,
        isLoading: false,
      }));
      logger.info(`✅ Updated store: ${updatedStore.name}`);
      return updatedStore;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update store';
      logger.error('❌ Failed to update store', { error: errorMessage });
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  /**
   * Delete a store
   */
  deleteStore: async (id: number) => {
    logger.info(`Deleting store: ${id}`);
    set({ isLoading: true, error: null });
    try {
      await storeService.deleteStore(id);
      set((state) => ({
        stores: state.stores.filter((s) => s.id !== id),
        currentStore: state.currentStore?.id === id ? null : state.currentStore,
        isLoading: false,
      }));
      logger.info(`✅ Deleted store: ${id}`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete store';
      logger.error('❌ Failed to delete store', { error: errorMessage });
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  /**
   * Set current store
   */
  setCurrentStore: (store: StoreDetail | null) => {
    set({ currentStore: store });
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },
}));
