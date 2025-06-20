import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';

// Mock the auth service
vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
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

// Test component to access context
const TestComponent = () => {
  const { user, login, logout, isAuthenticated, loading, error, register } = useAuth();
  
  return (
    <div>
      <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
      <div data-testid="isAuthenticated">{isAuthenticated.toString()}</div>
      <div data-testid="loading">{loading.toString()}</div>
      <div data-testid="error">{error || 'null'}</div>
      <button 
        onClick={() => login('testuser', 'password123')}
        data-testid="login-button"
      >
        Login
      </button>
      <button 
        onClick={() => register('testuser', 'test@example.com', 'password123', 'ANNOTATOR')}
        data-testid="register-button"
      >
        Register
      </button>
      <button onClick={logout} data-testid="logout-button">
        Logout
      </button>
    </div>
  );
};

const renderComponent = () => {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Initial State', () => {
    it('provides initial unauthenticated state', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null');
        expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
        expect(screen.getByTestId('error')).toHaveTextContent('null');
      });
    });

    it('loads user from localStorage on mount', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ADMIN',
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh'
      };
      
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user') return JSON.stringify(mockUser);
        if (key === 'token') return 'mock-token';
        return null;
      });

      // Mock getCurrentUser to return the user data
      (authService.getCurrentUser as any).mockResolvedValue({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ADMIN'
      });

      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify({
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'ADMIN'
        }));
        expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
      });
    });
  });

  describe('Login Functionality', () => {
    it('successfully logs in a user', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ADMIN'
      };

      (authService.login as any).mockResolvedValue({
        data: {
          user: mockUser,
          access: 'access-token',
          refresh: 'refresh-token'
        }
      });

      renderComponent();
      
      const loginButton = screen.getByTestId('login-button');
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'password123'
        });
        expect(localStorage.setItem).toHaveBeenCalled();
      });
    });

    it('handles login errors', async () => {
      (authService.login as any).mockRejectedValue(new Error('Invalid credentials'));

      renderComponent();
      
      const loginButton = screen.getByTestId('login-button');
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Login failed. Please try again.');
      });
    });
  });

  describe('Register Functionality', () => {
    it('successfully registers a user', async () => {
      (authService.register as any).mockResolvedValue({
        message: 'Registration successful'
      });

      renderComponent();
      
      const registerButton = screen.getByTestId('register-button');
      fireEvent.click(registerButton);

      await waitFor(() => {
        expect(authService.register).toHaveBeenCalledWith({
          username: 'testuser',
          email: 'test@example.com',
          password: 'password123',
          role: 'ANNOTATOR'
        });
      });
    });

    it('handles registration errors', async () => {
      (authService.register as any).mockRejectedValue(new Error('Registration failed'));

      renderComponent();
      
      const registerButton = screen.getByTestId('register-button');
      fireEvent.click(registerButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Registration failed. Please try again.');
      });
    });
  });

  describe('Logout Functionality', () => {
    it('successfully logs out a user', async () => {
      // First set up authenticated state
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ADMIN',
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh'
      };
      
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user') return JSON.stringify(mockUser);
        if (key === 'token') return 'mock-token';
        return null;
      });

      renderComponent();
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('true');
      });

      const logoutButton = screen.getByTestId('logout-button');
      fireEvent.click(logoutButton);

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null');
        expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
        expect(localStorage.removeItem).toHaveBeenCalledWith('user');
        expect(localStorage.removeItem).toHaveBeenCalledWith('token');
        expect(localStorage.removeItem).toHaveBeenCalledWith('refreshToken');
      });
    });
  });

  describe('Error Handling', () => {
    it('handles invalid localStorage data', async () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user') return 'invalid-json';
        return null;
      });

      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null');
        expect(screen.getByTestId('isAuthenticated')).toHaveTextContent('false');
      });
    });

    it('clears error state on successful operation', async () => {
      // First trigger an error
      (authService.login as any).mockRejectedValue(new Error('Invalid credentials'));

      renderComponent();
      
      const loginButton = screen.getByTestId('login-button');
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Login failed. Please try again.');
      });

      // Then perform successful login
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ADMIN'
      };

      (authService.login as any).mockResolvedValue({
        data: {
          user: mockUser,
          access: 'access-token',
          refresh: 'refresh-token'
        }
      });

      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('null');
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state during login', async () => {
      let resolveLogin: (value: any) => void;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });

      (authService.login as any).mockReturnValue(loginPromise);

      renderComponent();
      
      const loginButton = screen.getByTestId('login-button');
      fireEvent.click(loginButton);

      // Should show loading immediately
      expect(screen.getByTestId('loading')).toHaveTextContent('true');

      // Resolve the promise
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ADMIN'
      };

      resolveLogin!({
        data: {
          user: mockUser,
          access: 'access-token',
          refresh: 'refresh-token'
        }
      });

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });
    });
  });
});
