import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Pagination,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  useTheme,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Pause as PauseIcon,
  PlayArrow as UnpauseIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { authService } from '../../services/authService';
import { useAuth } from '../../contexts/AuthContext';

interface User {
  id: number;
  username: string;
  email: string;
  is_approved: boolean;
  role: string;
  date_joined?: string;
  last_login?: string | null;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [page, setPage] = useState(1);
  const [perPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [isApproved, setIsApproved] = useState(true);
  const [loading, setLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [pauseDialogOpen, setPauseDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const navigate = useNavigate();
  const theme = useTheme();
  const { user: currentUser } = useAuth();

  const fetchUsers = async () => {
    try {
      setLoading(true);
      console.log('Fetching users with params:', { page, perPage, isApproved });
      const response = await authService.getUsers(page, perPage, isApproved);
      
      // Filter out current admin user to prevent self-management
      const filteredUsers = response.users.filter(user => user.id !== currentUser?.id);
      
      setUsers(filteredUsers);
      setTotalPages(Math.ceil(response.pagination.total_users / perPage));
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, isApproved]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleApprove = async (userId: number) => {
    try {
      setLoading(true);
      console.log('Attempting to approve user with ID:', userId);
      await authService.approveUser(userId);
      fetchUsers();
    } catch (error) {
      console.error('Error approving user:', error);
      if (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof (error as any).response === 'object'
      ) {
        const response = (error as any).response;
        console.error('Response data:', response.data);
        console.error('Response status:', response.status);
        console.error('Response headers:', response.headers);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRoleUpdate = async (userId: number, newRole: 'ADMIN' | 'ANNOTATOR' | 'VERIFIER') => {
    try {
      setLoading(true);
      await authService.updateUserRole(userId, newRole);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user role:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (userId: number) => {
    try {
      setLoading(true);
      console.log('Attempting to reject user with ID:', userId);
      await authService.rejectUser(userId);
      setRejectDialogOpen(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (error) {
      console.error('Error rejecting user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (userId: number) => {
    try {
      setLoading(true);
      console.log('Attempting to delete user with ID:', userId);
      await authService.deleteUser(userId);
      setDeleteDialogOpen(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async (userId: number) => {
    try {
      setLoading(true);
      console.log('Attempting to pause/unpause user with ID:', userId);
      await authService.pauseUser(userId);
      setPauseDialogOpen(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (error) {
      console.error('Error pausing user:', error);
    } finally {
      setLoading(false);
    }
  };

  const openDeleteDialog = (user: User) => {
    setSelectedUser(user);
    setDeleteDialogOpen(true);
  };

  const openPauseDialog = (user: User) => {
    setSelectedUser(user);
    setPauseDialogOpen(true);
  };

  const openRejectDialog = (user: User) => {
    setSelectedUser(user);
    setRejectDialogOpen(true);
  };

  const handleBackToDashboard = () => {
    navigate('/superuser');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-4">
                <Tooltip title="Back to Dashboard">
                  <IconButton
                    onClick={handleBackToDashboard}
                    className="text-gray-600 hover:text-gray-800"
                    size="small"
                  >
                    <ArrowBackIcon />
                  </IconButton>
                </Tooltip>
                <div>
                  <h2 className="text-2xl font-semibold text-gray-900">User Management</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Manage users (excluding your own account for security)
                  </p>
                </div>
              </div>
              <FormControl sx={{ minWidth: 200 }}>
                <InputLabel>Filter by Status</InputLabel>
                <Select
                  value={isApproved ? 'approved' : 'pending'}
                  label="Filter by Status"
                  onChange={(e) => setIsApproved(e.target.value === 'approved')}
                  size="small"
                >
                  <MenuItem value="approved">Approved</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                </Select>
              </FormControl>
            </div>
          </div>

          <div className="overflow-x-auto">
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow className="bg-gray-50">
                    <TableCell className="font-semibold">Username</TableCell>
                    <TableCell className="font-semibold">Email</TableCell>
                    <TableCell className="font-semibold">Role</TableCell>
                    <TableCell className="font-semibold">Status</TableCell>
                    <TableCell className="font-semibold">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id} className="hover:bg-gray-50">
                      <TableCell>{user.username}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Select
                          value={user.role}
                          onChange={(e) => handleRoleUpdate(user.id, e.target.value as 'ADMIN' | 'ANNOTATOR' | 'VERIFIER')}
                          size="small"
                          className="min-w-[120px]"
                        >
                          <MenuItem value="ADMIN">Admin</MenuItem>
                          <MenuItem value="ANNOTATOR">Annotator</MenuItem>
                          <MenuItem value="VERIFIER">Verifier</MenuItem>
                        </Select>
                      </TableCell>
                      <TableCell>
                        {user.is_approved ? (
                          <span className="px-2 py-1 text-xs font-medium text-green-800 bg-green-100 rounded-full">
                            Approved
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs font-medium text-yellow-800 bg-yellow-100 rounded-full">
                            Pending
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {!user.is_approved ? (
                            <>
                              <Tooltip title="Approve User">
                                <IconButton
                                  onClick={() => handleApprove(user.id)}
                                  className="text-green-600 hover:text-green-700"
                                  size="small"
                                >
                                  <CheckIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Reject User">
                                <IconButton
                                  onClick={() => openRejectDialog(user)}
                                  className="text-red-600 hover:text-red-700"
                                  size="small"
                                >
                                  <CloseIcon />
                                </IconButton>
                              </Tooltip>
                            </>
                          ) : (
                            <>
                              <Tooltip title={user.is_approved ? 'Pause User' : 'Unpause User'}>
                                <IconButton
                                  onClick={() => openPauseDialog(user)}
                                  className="text-orange-600 hover:text-orange-700"
                                  size="small"
                                >
                                  {user.is_approved ? <PauseIcon /> : <UnpauseIcon />}
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete User">
                                <IconButton
                                  onClick={() => openDeleteDialog(user)}
                                  className="text-red-600 hover:text-red-700"
                                  size="small"
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Tooltip>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </div>

          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex justify-center">
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, value) => handlePageChange(value)}
                color="primary"
                size="small"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">Delete User</DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete user "{selectedUser?.username}"? This action cannot be undone and will
            permanently remove all user data.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} color="primary">
            Cancel
          </Button>
          <Button
            onClick={() => selectedUser && handleDelete(selectedUser.id)}
            color="error"
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Pause Confirmation Dialog */}
      <Dialog
        open={pauseDialogOpen}
        onClose={() => setPauseDialogOpen(false)}
        aria-labelledby="pause-dialog-title"
        aria-describedby="pause-dialog-description"
      >
        <DialogTitle id="pause-dialog-title">
          {selectedUser?.is_approved ? 'Pause User' : 'Unpause User'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="pause-dialog-description">
            Are you sure you want to {selectedUser?.is_approved ? 'pause' : 'unpause'} user "{selectedUser?.username}"?
            {selectedUser?.is_approved
              ? ' This will prevent them from logging in until they are unpaused.'
              : ' This will allow them to log in again.'}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPauseDialogOpen(false)} color="primary">
            Cancel
          </Button>
          <Button
            onClick={() => selectedUser && handlePause(selectedUser.id)}
            color="warning"
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Processing...' : selectedUser?.is_approved ? 'Pause' : 'Unpause'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reject Confirmation Dialog */}
      <Dialog
        open={rejectDialogOpen}
        onClose={() => setRejectDialogOpen(false)}
        aria-labelledby="reject-dialog-title"
        aria-describedby="reject-dialog-description"
      >
        <DialogTitle id="reject-dialog-title">Reject User</DialogTitle>
        <DialogContent>
          <DialogContentText id="reject-dialog-description">
            Are you sure you want to reject user "{selectedUser?.username}"? This action will permanently remove
            their account and they will need to register again if they want to use the system.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectDialogOpen(false)} color="primary">
            Cancel
          </Button>
          <Button
            onClick={() => selectedUser && handleReject(selectedUser.id)}
            color="error"
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Rejecting...' : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default UserManagement;