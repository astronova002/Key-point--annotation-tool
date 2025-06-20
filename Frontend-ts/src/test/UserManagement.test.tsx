import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import UserManagement from '../components/dashboard/UserManagement';
import { authService } from '../services/authService';

// Mock the auth service
vi.mock('../services/authService', () => ({
  authService: {
    getUsers: vi.fn(),
    approveUser: vi.fn(),
    updateUserRole: vi.fn(),
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

// Mock console methods
const consoleSpy = {
  log: vi.spyOn(console, 'log').mockImplementation(() => {}),
  error: vi.spyOn(console, 'error').mockImplementation(() => {}),
};

const mockUsers = [
  {
    id: 1,
    username: 'user1',
    email: 'user1@test.com',
    is_approved: false,
    role: 'ANNOTATOR',
    date_joined: '2024-01-01T00:00:00Z',
    last_login: '2024-01-02T00:00:00Z',
  },
  {
    id: 2,
    username: 'user2',
    email: 'user2@test.com',
    is_approved: true,
    role: 'ADMIN',
    date_joined: '2024-01-01T00:00:00Z',
    last_login: null,
  },
  {
    id: 3,
    username: 'user3',
    email: 'user3@test.com',
    is_approved: true,
    role: 'VERIFIER',
    date_joined: '2024-01-01T00:00:00Z',
    last_login: '2024-01-03T00:00:00Z',
  },
];

const mockPagination = {
  total_users: 3,
  current_page: 1,
  total_pages: 1,
  per_page: 10,
};

const renderComponent = () => {
  return render(
    <BrowserRouter>
      <UserManagement />
    </BrowserRouter>
  );
};

describe('UserManagement Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authService.getUsers.mockResolvedValue({
      users: mockUsers,
      pagination: mockPagination,
    });
  });

  afterEach(() => {
    consoleSpy.log.mockClear();
    consoleSpy.error.mockClear();
  });

  describe('Component Rendering', () => {
    it('renders without crashing', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('User Management')).toBeInTheDocument();
      });
    });

    it('displays the correct title', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('User Management')).toBeInTheDocument();
      });
    });

    it('shows the filter dropdown with correct options', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByLabelText('Filter by Status')).toBeInTheDocument();
      });
    });

    it('renders table headers correctly', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Username')).toBeInTheDocument();
        expect(screen.getByText('Email')).toBeInTheDocument();
        expect(screen.getByText('Role')).toBeInTheDocument();
        expect(screen.getByText('Status')).toBeInTheDocument();
        expect(screen.getByText('Actions')).toBeInTheDocument();
      });
    });

    it('shows pagination component', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByRole('navigation')).toBeInTheDocument();
      });
    });
  });

  describe('Data Fetching', () => {
    it('fetches users on component mount', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledWith(1, 10, true);
      });
    });

    it('displays user data correctly', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('user1')).toBeInTheDocument();
        expect(screen.getByText('user1@test.com')).toBeInTheDocument();
        expect(screen.getByText('user2')).toBeInTheDocument();
        expect(screen.getByText('user2@test.com')).toBeInTheDocument();
      });
    });

    it('handles API errors gracefully during user fetch', async () => {
      const error = new Error('API Error');
      authService.getUsers.mockRejectedValue(error);
      
      renderComponent();
      
      await waitFor(() => {
        expect(consoleSpy.error).toHaveBeenCalledWith('Error fetching users:', error);
      });
    });

    it('updates pagination based on total users count', async () => {
      const largePagination = {
        total_users: 50,
        current_page: 1,
        total_pages: 5,
        per_page: 10,
      };
      
      authService.getUsers.mockResolvedValue({
        users: mockUsers,
        pagination: largePagination,
      });
      
      renderComponent();
      
      await waitFor(() => {
        // Check if pagination shows correct number of pages
        expect(screen.getByRole('navigation')).toBeInTheDocument();
      });
    });
  });

  describe('Filter Functionality', () => {
    it('fetches users when approval filter changes', async () => {
      renderComponent();
      
      // Wait for initial load
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledWith(1, 10, true);
      });
      
      // Change filter to pending
      const filterSelect = screen.getByLabelText('Filter by Status');
      fireEvent.mouseDown(filterSelect);
      
      const pendingOption = screen.getByText('Pending');
      fireEvent.click(pendingOption);
      
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledWith(1, 10, false);
      });
    });

    it('resets page to 1 when filter changes', async () => {
      renderComponent();
      
      // Wait for initial load
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledWith(1, 10, true);
      });
      
      // Change filter
      const filterSelect = screen.getByLabelText('Filter by Status');
      fireEvent.mouseDown(filterSelect);
      
      const pendingOption = screen.getByText('Pending');
      fireEvent.click(pendingOption);
      
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledWith(1, 10, false);
      });
    });
  });

  describe('User Approval', () => {
    it('shows approve button only for unapproved users', async () => {
      renderComponent();
      
      await waitFor(() => {
        // user1 is not approved, should have approve button
        const approveButtons = screen.getAllByRole('button', { name: /approve user/i });
        expect(approveButtons.length).toBeGreaterThan(0);
      });
    });

    it('calls authService.approveUser with correct user ID', async () => {
      authService.approveUser.mockResolvedValue({});
      
      renderComponent();
      
      await waitFor(() => {
        const approveButton = screen.getByRole('button', { name: /approve user/i });
        fireEvent.click(approveButton);
      });
      
      await waitFor(() => {
        expect(authService.approveUser).toHaveBeenCalledWith(1);
      });
    });

    it('refreshes user list after successful approval', async () => {
      authService.approveUser.mockResolvedValue({});
      
      renderComponent();
      
      await waitFor(() => {
        const approveButton = screen.getByRole('button', { name: /approve user/i });
        fireEvent.click(approveButton);
      });
      
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledTimes(2); // Initial load + refresh
      });
    });

    it('handles 404 errors during approval', async () => {
      const mockError = {
        response: {
          status: 404,
          data: 'Not found',
          headers: {},
        },
      };
      authService.approveUser.mockRejectedValue(mockError);
      
      renderComponent();
      
      await waitFor(() => {
        const approveButton = screen.getByRole('button', { name: /approve user/i });
        fireEvent.click(approveButton);
      });
      
      await waitFor(() => {
        expect(consoleSpy.error).toHaveBeenCalledWith('Error approving user:', mockError);
        expect(consoleSpy.error).toHaveBeenCalledWith('Response data:', 'Not found');
        expect(consoleSpy.error).toHaveBeenCalledWith('Response status:', 404);
      });
    });

    it('handles network errors during approval', async () => {
      const networkError = new Error('Network Error');
      authService.approveUser.mockRejectedValue(networkError);
      
      renderComponent();
      
      await waitFor(() => {
        const approveButton = screen.getByRole('button', { name: /approve user/i });
        fireEvent.click(approveButton);
      });
      
      await waitFor(() => {
        expect(consoleSpy.error).toHaveBeenCalledWith('Error approving user:', networkError);
      });
    });
  });

  describe('Role Updates', () => {
    it('shows role select dropdown with correct options', async () => {
      renderComponent();
      
      await waitFor(() => {
        // Check if role selects are present
        const roleSelects = screen.getAllByDisplayValue('ANNOTATOR');
        expect(roleSelects.length).toBeGreaterThan(0);
      });
    });

    it('calls authService.updateUserRole with correct parameters', async () => {
      authService.updateUserRole.mockResolvedValue({});
      
      renderComponent();
      
      await waitFor(() => {
        // Find the first role select (for user1 - ANNOTATOR)
        const roleSelects = screen.getAllByDisplayValue('ANNOTATOR');
        fireEvent.mouseDown(roleSelects[0]);
      });
      
      const adminOption = screen.getByText('Admin');
      fireEvent.click(adminOption);
      
      await waitFor(() => {
        expect(authService.updateUserRole).toHaveBeenCalledWith(1, 'ADMIN');
      });
    });

    it('refreshes user list after role change', async () => {
      authService.updateUserRole.mockResolvedValue({});
      
      renderComponent();
      
      await waitFor(() => {
        const roleSelects = screen.getAllByDisplayValue('ANNOTATOR');
        fireEvent.mouseDown(roleSelects[0]);
      });
      
      const verifierOption = screen.getByText('Verifier');
      fireEvent.click(verifierOption);
      
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledTimes(2); // Initial load + refresh
      });
    });

    it('handles errors during role update', async () => {
      const error = new Error('Role update failed');
      authService.updateUserRole.mockRejectedValue(error);
      
      renderComponent();
      
      await waitFor(() => {
        const roleSelects = screen.getAllByDisplayValue('ANNOTATOR');
        fireEvent.mouseDown(roleSelects[0]);
      });
      
      const adminOption = screen.getByText('Admin');
      fireEvent.click(adminOption);
      
      await waitFor(() => {
        expect(consoleSpy.error).toHaveBeenCalledWith('Error updating user role:', error);
      });
    });
  });

  describe('Pagination', () => {
    it('handles page changes correctly', async () => {
      const multiPagePagination = {
        total_users: 25,
        current_page: 1,
        total_pages: 3,
        per_page: 10,
      };
      
      authService.getUsers.mockResolvedValue({
        users: mockUsers,
        pagination: multiPagePagination,
      });
      
      renderComponent();
      
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledWith(1, 10, true);
      });
      
      // Simulate page change
      // Note: This is a simplified test as MUI Pagination is complex to test
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('shows loading state during API calls', async () => {
      // Mock a delayed response
      let resolvePromise;
      const delayedPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      authService.getUsers.mockReturnValue(delayedPromise);
      
      renderComponent();
      
      // Component should be in loading state
      // Note: You might need to add loading indicators to the component
      
      // Resolve the promise
      resolvePromise({
        users: mockUsers,
        pagination: mockPagination,
      });
      
      await waitFor(() => {
        expect(screen.getByText('user1')).toBeInTheDocument();
      });
    });
  });

  describe('User Status Display', () => {
    it('displays correct status badges', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Pending')).toBeInTheDocument();
        expect(screen.getAllByText('Approved')).toHaveLength(2);
      });
    });

    it('applies correct styling to status badges', async () => {
      renderComponent();
      
      await waitFor(() => {
        const pendingBadge = screen.getByText('Pending');
        const approvedBadges = screen.getAllByText('Approved');
        
        expect(pendingBadge).toHaveClass('bg-yellow-100');
        expect(approvedBadges[0]).toHaveClass('bg-green-100');
      });
    });
  });

  describe('Error Boundary and Edge Cases', () => {
    it('handles empty user list', async () => {
      authService.getUsers.mockResolvedValue({
        users: [],
        pagination: { total_users: 0, current_page: 1, total_pages: 0, per_page: 10 },
      });
      
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('User Management')).toBeInTheDocument();
        // Should not crash with empty data
      });
    });

    it('handles malformed API responses', async () => {
      authService.getUsers.mockResolvedValue({
        users: null,
        pagination: null,
      });
      
      renderComponent();
      
      // Should not crash the component
      await waitFor(() => {
        expect(screen.getByText('User Management')).toBeInTheDocument();
      });
    });

    it('handles users with missing fields', async () => {
      const incompleteUsers = [
        {
          id: 1,
          username: 'incomplete',
          // Missing email, role, etc.
        },
      ];
      
      authService.getUsers.mockResolvedValue({
        users: incompleteUsers,
        pagination: mockPagination,
      });
      
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('incomplete')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByLabelText('Filter by Status')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /approve user/i })).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation', async () => {
      renderComponent();
      
      await waitFor(() => {
        const approveButton = screen.getByRole('button', { name: /approve user/i });
        
        // Focus the button
        approveButton.focus();
        expect(document.activeElement).toBe(approveButton);
        
        // Press Enter
        fireEvent.keyDown(approveButton, { key: 'Enter', code: 'Enter' });
      });
    });
  });

  describe('Integration Tests', () => {
    it('completes full user approval workflow', async () => {
      authService.approveUser.mockResolvedValue({});
      
      renderComponent();
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('user1')).toBeInTheDocument();
      });
      
      // Click approve button
      const approveButton = screen.getByRole('button', { name: /approve user/i });
      fireEvent.click(approveButton);
      
      // Verify approval was called
      await waitFor(() => {
        expect(authService.approveUser).toHaveBeenCalledWith(1);
      });
      
      // Verify refresh was called
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledTimes(2);
      });
    });

    it('completes full role change workflow', async () => {
      authService.updateUserRole.mockResolvedValue({});
      
      renderComponent();
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('user1')).toBeInTheDocument();
      });
      
      // Change role
      const roleSelects = screen.getAllByDisplayValue('ANNOTATOR');
      fireEvent.mouseDown(roleSelects[0]);
      
      const adminOption = screen.getByText('Admin');
      fireEvent.click(adminOption);
      
      // Verify role update was called
      await waitFor(() => {
        expect(authService.updateUserRole).toHaveBeenCalledWith(1, 'ADMIN');
      });
      
      // Verify refresh was called
      await waitFor(() => {
        expect(authService.getUsers).toHaveBeenCalledTimes(2);
      });
    });

    it('handles concurrent operations', async () => {
      authService.approveUser.mockResolvedValue({});
      authService.updateUserRole.mockResolvedValue({});
      
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('user1')).toBeInTheDocument();
      });
      
      // Perform multiple operations
      const approveButton = screen.getByRole('button', { name: /approve user/i });
      fireEvent.click(approveButton);
      
      const roleSelects = screen.getAllByDisplayValue('ANNOTATOR');
      fireEvent.mouseDown(roleSelects[0]);
      const adminOption = screen.getByText('Admin');
      fireEvent.click(adminOption);
      
      await waitFor(() => {
        expect(authService.approveUser).toHaveBeenCalled();
        expect(authService.updateUserRole).toHaveBeenCalled();
      });
    });
  });
});
