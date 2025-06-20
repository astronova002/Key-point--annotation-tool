import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import PrivateRoute from '../components/PrivateRoute';
import { AuthProvider } from '../contexts/AuthContext';

// Mock authService
vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

// Test component to wrap in PrivateRoute
const TestComponent = () => <div>Protected Content</div>;

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock as any;

const renderPrivateRoute = (allowedRoles?: string[]) => {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <PrivateRoute allowedRoles={allowedRoles}>
          <TestComponent />
        </PrivateRoute>
      </MemoryRouter>
    </AuthProvider>
  );
};

describe('PrivateRoute Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Unauthenticated Access', () => {
    it('does not render children when not authenticated', () => {
      renderPrivateRoute();
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Authenticated Access', () => {
    beforeEach(() => {
      // Mock authenticated user in localStorage
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ADMIN',
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token'
      };
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', 'mock-token');
    });

    it('renders children when user is authenticated and no role required', async () => {
      renderPrivateRoute();
      
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });
    });

    it('renders children when user has required role', async () => {
      renderPrivateRoute(['ADMIN']);
      
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });
    });
  });

  describe('Role-based Access Control', () => {
    it('allows ADMIN access to admin routes', async () => {
      const mockUser = {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        role: 'ADMIN',
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token'
      };
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', 'mock-token');
      
      renderPrivateRoute(['ADMIN']);
      
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });
    });

    it('allows ANNOTATOR access to annotator routes', async () => {
      const mockUser = {
        id: 1,
        username: 'annotator',
        email: 'annotator@example.com',
        role: 'ANNOTATOR',
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token'
      };
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', 'mock-token');
      
      renderPrivateRoute(['ANNOTATOR']);
      
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state during authentication check', () => {
      // Remove user from localStorage to simulate loading state
      localStorage.removeItem('user');
      
      renderPrivateRoute();
      
      // During loading, component should not show protected content
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });
});
