/**
 * Authentication Store (Zustand)
 * 
 * Global state management for authentication
 */

import { create } from 'zustand';
import type { AuthState, RegisterRequest } from '../types/auth';
import { authService } from '../services/authService';

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: false,
  isLoading: false,
  error: null,

  /**
   * Login user
   */
  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.login({ username, password });
      
      // Store token
      localStorage.setItem('access_token', response.access_token);
      
      // Fetch user profile
      const user = await authService.getCurrentUser();
      
      set({
        user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  /**
   * Register new user
   */
  register: async (data: RegisterRequest) => {
    set({ isLoading: true, error: null });
    try {
      await authService.register(data);
      
      // Auto-login after registration
      await useAuthStore.getState().login(data.username, data.password);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  /**
   * Logout user
   */
  logout: () => {
    authService.logout();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    });
  },

  /**
   * Fetch current user (for app initialization)
   */
  fetchCurrentUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    set({ isLoading: true });
    try {
      const user = await authService.getCurrentUser();
      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      // Token invalid, clear it
      localStorage.removeItem('access_token');
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },
}));
