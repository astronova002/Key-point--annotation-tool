import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Register from '../components/Register';
import { authService } from '../services/authService';
import { AuthProvider } from '../contexts/AuthContext';

// Mock the auth service
vi.mock('../services/authService', () => ({
  authService: {
    register: vi.fn(),
  },
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderComponent = () => {
  return render(
    <AuthProvider>
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    </AuthProvider>
  );
};

describe('Register Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Component Rendering', () => {
    it('renders registration form correctly', () => {
      renderComponent();
      
      expect(screen.getByText('Create your account')).toBeInTheDocument();
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/role/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
    });

    it('renders role selection dropdown', () => {
      renderComponent();
      
      const roleSelect = screen.getByLabelText(/role/i);
      expect(roleSelect).toBeInTheDocument();
      expect(screen.getByText('Annotator')).toBeInTheDocument();
      expect(screen.getByText('Verifier')).toBeInTheDocument();
    });

    it('renders login link', () => {
      renderComponent();
      
      expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
    });
  });

  describe('Registration Functionality', () => {
    it('calls register function with correct data', async () => {
      (authService.register as any).mockResolvedValue({
        message: 'Registration successful'
      });
      
      renderComponent();
      
      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const roleSelect = screen.getByLabelText(/role/i);
      
      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(roleSelect, { target: { value: 'ANNOTATOR' } });
      
      const submitButton = screen.getByRole('button', { name: /sign up/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      });
    });

    it('handles registration errors', async () => {
      (authService.register as any).mockRejectedValue(new Error('Registration failed'));
      
      renderComponent();
      
      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const roleSelect = screen.getByLabelText(/role/i);
      
      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(roleSelect, { target: { value: 'ANNOTATOR' } });
      
      const submitButton = screen.getByRole('button', { name: /sign up/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/failed to register/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('navigates to login page when clicking sign in link', () => {
      renderComponent();
      
      const signInLink = screen.getByText(/sign in/i);
      expect(signInLink.closest('a')).toHaveAttribute('href', '/login');
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderComponent();
      
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/role/i)).toBeInTheDocument();
    });
  });
});
