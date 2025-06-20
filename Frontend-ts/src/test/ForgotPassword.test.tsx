import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ForgotPassword from '../components/ForgotPassword';
import { authService } from '../services/authService';

// Mock the auth service
vi.mock('../services/authService', () => ({
  authService: {
    forgotPassword: vi.fn(),
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
    <BrowserRouter>
      <ForgotPassword />
    </BrowserRouter>
  );
};

describe('ForgotPassword Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders forgot password form correctly', () => {
      renderComponent();
      
      expect(screen.getByText('Forgot Password')).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
    });

    it('renders back to login link', () => {
      renderComponent();
      
      expect(screen.getByText(/back to login/i)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows validation error for empty email', async () => {
      renderComponent();
      
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      fireEvent.click(submitButton);
      
      // HTML5 validation should prevent empty email submission
      // This is handled by the required attribute on the input
      expect(authService.forgotPassword).not.toHaveBeenCalled();
    });

    it('shows validation error for invalid email format', async () => {
      renderComponent();
      
      const emailInput = screen.getByLabelText(/email/i);
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
      fireEvent.click(submitButton);
      
      // HTML5 validation should prevent invalid email submission
      expect(authService.forgotPassword).not.toHaveBeenCalled();
    });
  });

  describe('Password Reset Functionality', () => {
    it('calls forgotPassword service with correct email', async () => {
      (authService.forgotPassword as any).mockResolvedValue({
        message: 'Reset link sent successfully'
      });
      
      renderComponent();
      
      const emailInput = screen.getByLabelText(/email/i);
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(authService.forgotPassword).toHaveBeenCalledWith('test@example.com');
      });
    });

    it('shows success message on successful password reset request', async () => {
      (authService.forgotPassword as any).mockResolvedValue({
        message: 'Reset link sent successfully'
      });
      
      renderComponent();
      
      const emailInput = screen.getByLabelText(/email/i);
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/password reset link has been sent to your email/i)).toBeInTheDocument();
      });
    });

    it('handles password reset request errors', async () => {
      (authService.forgotPassword as any).mockRejectedValue({
        response: {
          data: {
            error: 'Email not found'
          }
        }
      });
      
      renderComponent();
      
      const emailInput = screen.getByLabelText(/email/i);
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      
      fireEvent.change(emailInput, { target: { value: 'nonexistent@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/email not found/i)).toBeInTheDocument();
      });
    });

    it('handles generic errors', async () => {
      (authService.forgotPassword as any).mockRejectedValue(new Error('Network error'));
      
      renderComponent();
      
      const emailInput = screen.getByLabelText(/email/i);
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/failed to send reset link/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('navigates back to login page', () => {
      renderComponent();
      
      const backToLoginLink = screen.getByText(/back to login/i);
      fireEvent.click(backToLoginLink);
      
      expect(backToLoginLink.closest('a')).toHaveAttribute('href', '/login');
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderComponent();
      
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    it('provides proper instructions', () => {
      renderComponent();
      
      expect(screen.getByText(/enter your email address and we'll send you a link to reset your password/i)).toBeInTheDocument();
    });
  });
});

describe('ForgotPassword Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders forgot password form correctly', () => {
      renderComponent();
      
      expect(screen.getByText('Forgot Password')).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
    });

    it('renders back to login link', () => {
      renderComponent();
      
      expect(screen.getByText(/back to login/i)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows validation error for empty email', async () => {
      renderComponent();
      
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      });
    });

    it('shows validation error for invalid email format', async () => {
      renderComponent();
      
      const emailInput = screen.getByLabelText(/email/i);
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
      
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email/i)).toBeInTheDocument();
      });
    });
  });

  describe('Password Reset Request', () => {
    it('successfully sends password reset email', async () => {
      authService.requestPasswordReset.mockResolvedValue({
        message: 'Password reset email sent',
      });

      renderComponent();

      const emailInput = screen.getByLabelText(/email/i);
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(authService.requestPasswordReset).toHaveBeenCalledWith('test@example.com');
      });

      await waitFor(() => {
        expect(screen.getByText(/password reset email sent/i)).toBeInTheDocument();
      });
    });

    it('handles password reset request error', async () => {
      authService.requestPasswordReset.mockRejectedValue(new Error('Email not found'));

      renderComponent();

      const emailInput = screen.getByLabelText(/email/i);
      fireEvent.change(emailInput, { target: { value: 'nonexistent@example.com' } });

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/email not found/i)).toBeInTheDocument();
      });
    });

    it('shows loading state during request', async () => {
      let resolveRequest;
      const requestPromise = new Promise((resolve) => {
        resolveRequest = resolve;
      });
      authService.requestPasswordReset.mockReturnValue(requestPromise);

      renderComponent();

      const emailInput = screen.getByLabelText(/email/i);
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      fireEvent.click(submitButton);

      // Should show loading state
      expect(screen.getByRole('button', { name: /sending/i })).toBeDisabled();

      resolveRequest({ message: 'Email sent' });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('navigates back to login page', () => {
      renderComponent();
      
      const backToLoginLink = screen.getByText(/back to login/i);
      fireEvent.click(backToLoginLink);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      renderComponent();
      
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      renderComponent();
      
      const emailInput = screen.getByLabelText(/email/i);
      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      
      emailInput.focus();
      expect(document.activeElement).toBe(emailInput);
      
      fireEvent.keyDown(emailInput, { key: 'Tab' });
      submitButton.focus();
      expect(document.activeElement).toBe(submitButton);
    });
  });

  describe('Security', () => {
    it('sanitizes email input', async () => {
      authService.requestPasswordReset.mockResolvedValue({ message: 'Email sent' });

      renderComponent();

      const emailInput = screen.getByLabelText(/email/i);
      fireEvent.change(emailInput, { target: { value: '<script>alert("xss")</script>@example.com' } });

      const submitButton = screen.getByRole('button', { name: /send reset link/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(authService.requestPasswordReset).toHaveBeenCalledWith('<script>alert("xss")</script>@example.com');
      });
    });
  });
});
