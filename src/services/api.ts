/**
 * SAWS API Client
 *
 * Saudi AgriDrought Warning System
 * Axios instance with interceptors for API communication
 */

import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { toast } from 'sonner';

// API base URL - configurable via environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Create configured axios instance
 */
export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

/**
 * Request interceptor - adds auth token
 */
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem('saws_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request ID for tracing
    config.headers['X-Request-ID'] = crypto.randomUUID?.() || Math.random().toString(36);

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - handles errors and response formatting
 */
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Add process time header to response data if available
    const processTime = response.headers['x-process-time'];
    if (processTime && response.data) {
      (response.data as any)._meta = {
        processTime: parseFloat(processTime),
        requestId: response.headers['x-request-id'],
      };
    }

    return response;
  },
  (error: AxiosError) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const data = error.response.data as any;
      const status = error.response.status;

      // Extract error message
      const errorMessage = data?.error?.message || data?.message || 'An error occurred';

      // Show toast notification
      switch (status) {
        case 401:
          toast.error('Authentication required. Please log in.');
          // Redirect to login or trigger re-authentication
          break;
        case 403:
          toast.error('You do not have permission to perform this action.');
          break;
        case 404:
          toast.error('The requested resource was not found.');
          break;
        case 429:
          toast.error('Too many requests. Please try again later.');
          break;
        case 500:
          toast.error('A server error occurred. Please try again later.');
          break;
        default:
          toast.error(errorMessage);
      }

      return Promise.reject({
        status,
        message: errorMessage,
        code: data?.error?.code,
        data: data?.error,
      });
    } else if (error.request) {
      // Request was made but no response received
      toast.error('Network error. Please check your connection.');
      return Promise.reject({
        message: 'Network error',
        originalError: error,
      });
    } else {
      // Error in request configuration
      toast.error('An unexpected error occurred.');
      return Promise.reject({
        message: error.message,
        originalError: error,
      });
    }
  }
);

/**
 * API wrapper functions for common operations
 */
export const apiClient = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) =>
    api.get<T>(url, config).then((res) => res.data),

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    api.post<T>(url, data, config).then((res) => res.data),

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    api.put<T>(url, data, config).then((res) => res.data),

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    api.patch<T>(url, data, config).then((res) => res.data),

  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    api.delete<T>(url, config).then((res) => res.data),
};

/**
 * Pagination helper
 */
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  total: number;
  skip: number;
  limit: number;
  items: T[];
}

/**
 * Error types
 */
export interface ApiError {
  status?: number;
  message: string;
  code?: string;
  data?: any;
}

/**
 * Check if error is an API error
 */
export function isApiError(error: any): error is ApiError {
  return error && typeof error.message === 'string';
}

export default api;
