/**
 * Authentication Store (Zustand)
 * 
 * Global state management for authentication
 */

import { create } from 'zustand';
import type { AuthState, RegisterRequest } from '../types/auth';
import { authService } from '../services/authService';
import { logger } from '../utils/logger';

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: false,
  isLoading: true, // Start as true while we check authentication
  error: null,

  /**
   * Login user
   */
  login: async (username: string, password: string) => {
    logger.info('Login attempt', { username });
    set({ isLoading: true, error: null });
    try {
      const response = await authService.login({ username, password });
      
      // Store both tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      logger.debug('Tokens stored in localStorage');
      
      // Fetch user profile
      const user = await authService.getCurrentUser();
      
      set({
        user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      logger.info('✅ Login successful', { userId: user.id, username: user.username });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      logger.error('❌ Login failed', { username, error: errorMessage });
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
    logger.info('Registration attempt', { username: data.username, email: data.email });
    set({ isLoading: true, error: null });
    try {
      await authService.register(data);
      logger.info('✅ Registration successful, attempting auto-login', { username: data.username });
      
      // Auto-login after registration
      await useAuthStore.getState().login(data.username, data.password);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      logger.error('❌ Registration failed', { username: data.username, error: errorMessage });
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
    logger.info('User logging out');
    authService.logout();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    });
    logger.info('✅ Logout successful');
  },

  /**
   * Fetch current user (for app initialization)
   */
  fetchCurrentUser: async () => {
    logger.debug('Checking authentication status...');
    // Ensure loading state is set (in case it was changed)
    set({ isLoading: true });
    
    // Minimum display time for loading screen (so users can see the beautiful animation!)
    const minLoadTime = new Promise(resolve => setTimeout(resolve, 800));
    
    const token = localStorage.getItem('access_token');
    if (!token) {
      logger.info('No token found, user not authenticated');
      await minLoadTime; // Wait for minimum time
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const [user] = await Promise.all([
        authService.getCurrentUser(),
        minLoadTime // Ensure minimum loading time
      ]);
      
      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      logger.info('✅ User authenticated', { userId: user.id, username: user.username });
    } catch (error) {
      logger.warn('Token invalid or expired, clearing authentication');
      await minLoadTime; // Wait for minimum time
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
   * Refresh access token
   */
  refreshToken: async () => {
    logger.debug('Attempting to refresh access token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
      logger.warn('No refresh token found');
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const response = await authService.refreshToken(refreshToken);
      
      // Store new tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      set({
        token: response.access_token,
        error: null,
      });
      
      logger.info('✅ Token refresh successful');
    } catch (error) {
      logger.error('❌ Token refresh failed', error);
      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      });
      throw error;
    }
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },
}));
