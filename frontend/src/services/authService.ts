/**
 * Authentication Service
 * 
 * API calls for authentication endpoints
 */

import api from './api';
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '../types/auth';

export const authService = {
  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    // Backend expects form data for OAuth2
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await api.post<AuthResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/api/v1/auth/register', data);
    return response.data;
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/api/v1/auth/me');
    return response.data;
  },

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /**
   * Logout (clear tokens)
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};
