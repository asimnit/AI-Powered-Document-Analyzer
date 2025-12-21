/**
 * API Configuration
 * 
 * Base axios instance with interceptors for authentication
 */

import axios from 'axios';
import { logger } from '../utils/logger';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log API request
    logger.apiRequest(
      config.method?.toUpperCase() || 'GET',
      config.url || '',
      config.data
    );
    
    return config;
  },
  (error) => {
    logger.error('API request error', error);
    return Promise.reject(error);
  }
);

// Response interceptor - Handle 401 errors and auto-refresh tokens
api.interceptors.response.use(
  (response) => {
    // Log successful API response
    logger.apiResponse(
      response.config.method?.toUpperCase() || 'GET',
      response.config.url || '',
      response.status,
      response.data
    );
    
    return response;
  },
  async (error) => {
    const status = error.response?.status;
    const url = error.config?.url || '';
    const method = error.config?.method?.toUpperCase() || 'GET';
    const originalRequest = error.config;
    
    // Log API error
    logger.apiResponse(method, url, status, error.response?.data);
    
    if (status === 401) {
      // Don't try to refresh on auth endpoints
      const isAuthAttempt = url.includes('/auth/login') || 
                           url.includes('/auth/register') ||
                           url.includes('/auth/refresh');
      
      if (!isAuthAttempt && !originalRequest._retry) {
        // Try to refresh token once
        originalRequest._retry = true;
        
        try {
          logger.info('Access token expired, attempting refresh...');
          
          // Get refresh token
          const refreshToken = localStorage.getItem('refresh_token');
          if (!refreshToken) {
            throw new Error('No refresh token available');
          }
          
          // Call refresh endpoint directly (avoid circular dependency)
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          // Store new tokens
          const { access_token, refresh_token: new_refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', new_refresh_token);
          
          // Update authorization header for retry
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          
          logger.info('✅ Token refreshed successfully, retrying original request');
          
          // Retry the original request with new token
          return api(originalRequest);
          
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          logger.error('❌ Token refresh failed, redirecting to login', refreshError);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else if (isAuthAttempt) {
        // Auth attempt failed, don't redirect (let login page handle it)
        return Promise.reject(error);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
