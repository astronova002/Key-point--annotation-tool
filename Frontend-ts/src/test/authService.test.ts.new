import { vi, describe, it, expect, beforeEach } from 'vitest';
import { authService } from '../services/authService';
import axios from 'axios';

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock as any;

describe('AuthService', () => {
  let mockAxiosInstance: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockAxiosInstance = {
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    };
    (axios.create as any).mockReturnValue(mockAxiosInstance);
  });

  describe('Register', () => {
    it('successfully registers a user', async () => {
      const userData = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        role: 'ANNOTATOR' as const,
      };

      const expectedResponse = {
        users: [],
        pagination: {
          current_page: 1,
          total_pages: 1,
          total_users: 0,
          per_page: 10
        }
      };

      mockAxiosInstance.post.mockResolvedValue({
        data: expectedResponse,
      });

      const result = await authService.register(userData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('register/', userData);
      expect(result).toEqual(expectedResponse);
    });

    it('handles registration errors', async () => {
      const userData = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        role: 'ANNOTATOR' as const,
      };

      const errorResponse = {
        response: {
          data: { error: 'Username already exists' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(authService.register(userData)).rejects.toEqual(errorResponse);
    });
  });

  describe('Login', () => {
    it('successfully logs in a user', async () => {
      const credentials = {
        username: 'testuser',
        password: 'password123',
      };

      const expectedResponse = {
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'ADMIN',
        },
        access: 'access-token',
        refresh: 'refresh-token',
      };

      mockAxiosInstance.post.mockResolvedValue({
        data: expectedResponse,
      });

      const result = await authService.login(credentials.username, credentials.password);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('login/', credentials);
      expect(result).toEqual(expectedResponse.user);
      expect(localStorage.setItem).toHaveBeenCalled();
    });

    it('handles login failure', async () => {
      const credentials = {
        username: 'testuser',
        password: 'wrongpassword',
      };

      const errorResponse = {
        response: {
          data: { error: 'Invalid credentials' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(authService.login(credentials.username, credentials.password)).rejects.toThrow();
    });
  });

  describe('Logout', () => {
    it('clears user data from localStorage', async () => {
      await authService.logout();

      expect(localStorage.removeItem).toHaveBeenCalledWith('user');
      expect(localStorage.removeItem).toHaveBeenCalledWith('token');
      expect(localStorage.removeItem).toHaveBeenCalledWith('refreshToken');
    });
  });

  describe('User Management', () => {
    it('gets users with pagination', async () => {
      const expectedResponse = {
        users: [
          {
            id: 1,
            username: 'user1',
            email: 'user1@example.com',
            role: 'ADMIN',
            is_approved: true,
          },
        ],
        pagination: {
          current_page: 1,
          total_pages: 1,
          total_users: 1,
          per_page: 10,
        },
      };

      mockAxiosInstance.get.mockResolvedValue({
        data: expectedResponse,
      });

      const result = await authService.getUsers(1, 10, true);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('users/', {
        params: { page: 1, per_page: 10, approved: true }
      });
      expect(result).toEqual(expectedResponse);
    });

    it('approves a user', async () => {
      const userId = 1;
      const expectedResponse = { message: 'User approved successfully' };

      mockAxiosInstance.post.mockResolvedValue({
        data: expectedResponse,
      });

      const result = await authService.approveUser(userId);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(`users/${userId}/approve/`);
      expect(result).toEqual(expectedResponse);
    });

    it('updates user role', async () => {
      const userId = 1;
      const newRole = 'ADMIN' as const;
      const expectedResponse = { message: 'User role updated successfully' };

      mockAxiosInstance.put.mockResolvedValue({
        data: expectedResponse,
      });

      const result = await authService.updateUserRole(userId, newRole);

      expect(mockAxiosInstance.put).toHaveBeenCalledWith(`users/${userId}/role/`, { role: newRole });
      expect(result).toEqual(expectedResponse);
    });
  });

  describe('Password Reset', () => {
    it('requests password reset', async () => {
      const email = 'test@example.com';
      const expectedResponse = { message: 'Reset link sent successfully' };

      mockAxiosInstance.post.mockResolvedValue({
        data: expectedResponse,
      });

      const result = await authService.forgotPassword(email);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('forgot-password/', { email });
      expect(result).toEqual(expectedResponse);
    });

    it('resets password', async () => {
      const token = 'reset-token';
      const newPassword = 'newpassword123';
      const expectedResponse = { message: 'Password reset successfully' };

      mockAxiosInstance.post.mockResolvedValue({
        data: expectedResponse,
      });

      const result = await authService.resetPassword(token, newPassword);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('reset-password/', { 
        token, 
        new_password: newPassword 
      });
      expect(result).toEqual(expectedResponse);
    });
  });
});
