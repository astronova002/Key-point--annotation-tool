import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import App from '../App';
import { authService } from '../services/authService';

// Mock the auth service
vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    getUsers: vi.fn(),
    approveUser: vi.fn(),
    updateUserRole: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
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

const renderApp = () => {
  return render(<App />);
};

describe('End-to-End Application Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    (authService.getCurrentUser as any).mockResolvedValue(null);
  });

  describe('Landing Page', () => {
    it('renders landing page on root route', async () => {
      renderApp();
      
      await waitFor(() => {
        expect(screen.getByText(/welcome/i)).toBeInTheDocument();
      });
    });

    it('can navigate to login from landing page', async () => {
      renderApp();
      
      const loginButton = await screen.findByText(/sign in/i);
      fireEvent.click(loginButton);
      
      await waitFor(() => {
        expect(screen.getByText(/sign in/i)).toBeInTheDocument();
      });
    });

    it('can navigate to register from landing page', async () => {
      renderApp();
      
      const registerButton = await screen.findByText(/sign up/i);
      fireEvent.click(registerButton);
      
      await waitFor(() => {
        expect(screen.getByText(/create your account/i)).toBeInTheDocument();
      });
    });
  });

  describe('Authentication Flow', () => {
    it('shows login form when navigating to /login', async () => {
      // Mock window.location
      Object.defineProperty(window, 'location', {
        value: { pathname: '/login' },
        writable: true,
      });

      renderApp();
      
      await waitFor(() => {
        expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      });
    });

    it('shows register form when navigating to /register', async () => {
      Object.defineProperty(window, 'location', {
        value: { pathname: '/register' },
        writable: true,
      });

      renderApp();
      
      await waitFor(() => {
        expect(screen.getByText(/create your account/i)).toBeInTheDocument();
      });
    });
  });

  describe('Authentication State', () => {
    it('loads authenticated user from localStorage', async () => {
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

      (authService.getCurrentUser as any).mockResolvedValue({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ADMIN'
      });

      renderApp();
      
      // Should not show login form if authenticated
      await waitFor(() => {
        expect(screen.queryByText(/sign in/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('redirects to login when not authenticated and accessing protected route', async () => {
      Object.defineProperty(window, 'location', {
        value: { pathname: '/superuser' },
        writable: true,
      });

      renderApp();
      
      await waitFor(() => {
        expect(screen.getByText(/sign in/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles authentication errors gracefully', async () => {
      (authService.getCurrentUser as any).mockRejectedValue(new Error('Authentication failed'));
      
      renderApp();
      
      // Should still render the app without crashing
      await waitFor(() => {
        expect(screen.getByText(/welcome/i)).toBeInTheDocument();
      });
    });

    it('handles network errors during authentication', async () => {
      const networkError = new Error('Network error');
      (networkError as any).code = 'NETWORK_ERROR';
      
      (authService.getCurrentUser as any).mockRejectedValue(networkError);
      
      renderApp();
      
      await waitFor(() => {
        expect(screen.getByText(/welcome/i)).toBeInTheDocument();
      });
    });
  });

  describe('Routing', () => {
    it('shows unauthorized page for insufficient permissions', async () => {
      const mockUser = {
        id: 1,
        username: 'annotator',
        email: 'annotator@example.com',
        role: 'ANNOTATOR',
        accessToken: 'mock-token'
      };

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user') return JSON.stringify(mockUser);
        if (key === 'token') return 'mock-token';
        return null;
      });

      (authService.getCurrentUser as any).mockResolvedValue({
        id: 1,
        username: 'annotator',
        email: 'annotator@example.com',
        role: 'ANNOTATOR'
      });

      Object.defineProperty(window, 'location', {
        value: { pathname: '/superuser' },
        writable: true,
      });

      renderApp();
      
      await waitFor(() => {
        expect(screen.getByText(/unauthorized/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('can navigate between public routes', async () => {
      renderApp();
      
      // Start at landing page
      await waitFor(() => {
        expect(screen.getByText(/welcome/i)).toBeInTheDocument();
      });

      // Navigate to forgot password
      const forgotPasswordLink = screen.getByText(/forgot password/i);
      fireEvent.click(forgotPasswordLink);
      
      await waitFor(() => {
        expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
      });
    });
  });
});
