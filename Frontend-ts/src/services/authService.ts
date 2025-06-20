import axios from 'axios';
import { apiConfig } from '../config/api';

const API_URL = apiConfig.auth.status.replace('/status/', '/'); // Get base auth URL

// Define PaginatedResponse type if not already defined or imported
export interface PaginatedResponse<T = any> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

// Update the api instance configuration
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true // Enable sending cookies
});

// Add request interceptor to include auth token
api.interceptors.request.use(
    (config) => {
        const user = localStorage.getItem('user');
        if (user) {
            try {
                const { accessToken } = JSON.parse(user);
                if (accessToken && config.headers) {
                    config.headers.Authorization = `Bearer ${accessToken}`;
                    console.log('Adding authorization header:', `Bearer ${accessToken.substring(0, 20)}...`);
                } else {
                    console.warn('No accessToken found in user data');
                }
            } catch (error) {
                console.error('Error parsing user data:', error);
            }
        } else {
            console.warn('No user data found in localStorage');
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Prevent redirect loops - add a flag to track if we're already redirecting
let isRedirecting = false;

// Less aggressive response interceptor
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Only handle 401 errors and prevent retry loops
        if (error.response?.status === 401 && !originalRequest._retry && !isRedirecting) {
            originalRequest._retry = true;
            console.log('401 error detected, attempting token refresh...');

            try {
                const user = localStorage.getItem('user');
                if (!user) {
                    console.error('No user data in localStorage for refresh');
                    return Promise.reject(error);
                }

                const userData = JSON.parse(user);
                const { refreshToken } = userData;

                if (!refreshToken) {
                    console.error('No refresh token available');
                    return Promise.reject(error);
                }

                const response = await axios.post<{ access: string }>(`${apiConfig.auth.tokenRefresh}`, {
                    refresh: refreshToken
                }, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const { access } = response.data;

                if (!access) {
                    console.error('No access token in refresh response');
                    return Promise.reject(error);
                }

                const updatedUser = {
                    ...userData,
                    accessToken: access
                };
                localStorage.setItem('user', JSON.stringify(updatedUser));
                console.log('Token refreshed successfully');

                if (originalRequest.headers) {
                    originalRequest.headers.Authorization = `Bearer ${access}`;
                }

                return api(originalRequest);
            } catch (refreshError) {
                console.error('Token refresh failed:', refreshError);
                
                // Only clear storage and redirect if refresh actually failed with 401
                if (
                    typeof refreshError === 'object' &&
                    refreshError !== null &&
                    'response' in refreshError &&
                    (refreshError as any).response?.status === 401
                ) {
                    console.log('Refresh token expired, clearing session');
                    
                    // Prevent multiple simultaneous redirects
                    if (!isRedirecting) {
                        isRedirecting = true;
                        localStorage.removeItem('user');
                        
                        // Only redirect if not already on login page
                        if (window.location.pathname !== '/login') {
                            console.log('Redirecting to login page');
                            window.location.href = '/login';
                        } else {
                            console.log('Already on login page, not redirecting');
                            isRedirecting = false; // Reset flag if already on login
                        }
                    }
                }
                
                return Promise.reject(refreshError);
            }
        }
        
        // For non-401 errors or if already retried, just reject
        return Promise.reject(error);
    }
);

export interface LoginResponse {
    message: string;
    id: number;
    username: string;
    email: string;
    role: 'ADMIN' | 'ANNOTATOR' | 'VERIFIER';
    is_approved: boolean;
    accessToken: string;
    refreshToken: string;
}

export interface RegisterData {
    username: string;
    email: string;
    password: string;
    role?: 'ADMIN' | 'ANNOTATOR' | 'VERIFIER';
}

// Update the User interface to include tokens
export interface User {
    id: number;
    username: string;
    email: string;
    role: 'ADMIN' | 'ANNOTATOR' | 'VERIFIER';
    is_approved: boolean;
    accessToken?: string;
    refreshToken?: string;
}

class AuthService {
    // Debug method to inspect localStorage
    debugLocalStorage() {
        console.log('=== AuthService Debug Info ===');
        const user = localStorage.getItem('user');
        console.log('Raw user data:', user);
        if (user) {
            try {
                const userData = JSON.parse(user);
                console.log('Parsed user data:', userData);
                console.log('Has accessToken:', !!userData.accessToken);
                console.log('Has refreshToken:', !!userData.refreshToken);
                console.log('User role:', userData.role);
                console.log('User approved:', userData.is_approved);
            } catch (error) {
                console.error('Error parsing user data:', error);
            }
        } else {
            console.log('No user data in localStorage');
        }
        console.log('=== End Debug Info ===');
    }

    async register(data: RegisterData) {
        const response = await api.post('register/', data);
        return response.data as PaginatedResponse;
    }

    async login(username: string, password: string) {
        try {
            console.log('AuthService: Making login request');
            const response = await api.post<LoginResponse>('/login/', { username, password });
            console.log('AuthService: Login response:', response.data);
            
            // Handle the actual response format from your backend
            const userData = {
                id: response.data.id,
                username: response.data.username,
                email: response.data.email,
                role: response.data.role,
                is_approved: response.data.is_approved,
                accessToken: response.data.accessToken,
                refreshToken: response.data.refreshToken
            };
            
            localStorage.setItem('user', JSON.stringify(userData));
            console.log('AuthService: Stored user data in localStorage');
            
            // Return the user data for the context
            return userData;
        } catch (error) {
            console.error('AuthService: Login error:', error);
            throw error;
        }
    }

    // Safe session clearing without forced redirects
    clearSessionQuietly() {
        console.log('Clearing session data quietly...');
        
        // Clear all auth-related data
        const authKeys = ['user', 'token', 'access_token', 'refresh_token', 'accessToken', 'refreshToken'];
        authKeys.forEach(key => {
            localStorage.removeItem(key);
        });
        
        // Reset redirect flag
        isRedirecting = false;
        
        console.log('Session cleared without redirect');
    }

    // Improved logout method
    async logout() {
        console.log('authService - Logging out user');
        
        try {
            // Try to call logout endpoint
            await api.post('logout/');
            console.log('Logout API call successful');
        } catch (error) {
            console.warn('Logout API call failed, continuing with local cleanup:', error);
        }
        
        // Clear session data
        this.clearSessionQuietly();
        
        // Only redirect if not already on login page
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
    }

    // Add method to force clear all authentication data
    forceLogout() {
        console.log('authService - Force clearing all authentication data');
        
        // Clear all possible authentication keys
        const authKeys = ['user', 'token', 'access_token', 'refresh_token', 'accessToken', 'refreshToken'];
        authKeys.forEach(key => {
            localStorage.removeItem(key);
        });
        
        // Redirect to login
        window.location.href = '/login';
    }

    getCurrentUser(): User | null {
        try {
            const userStr = localStorage.getItem('user');
            if (!userStr) {
                return null;
            }

            const userData = JSON.parse(userStr);
            
            // More lenient validation - only check for essential fields
            if (!userData || !userData.id || !userData.username || !userData.email) {
                console.warn('getCurrentUser - Invalid user data structure');
                return null;
            }

            // Return user data even if tokens are missing - they might be refreshed later
            return {
                id: userData.id,
                username: userData.username,
                email: userData.email,
                role: userData.role || 'ANNOTATOR', // Default role
                is_approved: userData.is_approved !== false, // Default to approved
                accessToken: userData.accessToken,
                refreshToken: userData.refreshToken
            };
        } catch (error) {
            console.error('getCurrentUser - Error parsing user data:', error);
            return null;
        }
    }

    // Helper method to check if user has valid tokens
    hasValidTokens(): boolean {
        const userStr = localStorage.getItem('user');
        if (!userStr) return false;
        
        try {
            const userData = JSON.parse(userStr);
            return !!(userData.accessToken && userData.refreshToken);
        } catch {
            return false;
        }
    }

    // Add a helper method to validate tokens
    validateTokens(): boolean {
        const user = localStorage.getItem('user');
        if (!user) return false;

        try {
            const { accessToken, refreshToken } = JSON.parse(user);
            return !!(accessToken && refreshToken);
        } catch {
            return false;
        }
    }

    async requestPasswordReset(email: string) {
        const response = await api.post('forgot-password/', { email });
        return response.data;
    }

    async getAllUsers(page: number = 1, perPage: number = 10): Promise<PaginatedResponse> {
        return this.getUsers(page, perPage);
    }

    async getUserStatus() {
        const response = await api.get('status/');
        return response.data as PaginatedResponse;
    }

    async getPendingUsers() {
        const response = await api.get('pending-users/');
        return response.data as PaginatedResponse;
    }

    async approveUser(userId: number) {
        const response = await api.post(`approve-user/${userId}/`);
        return response.data;
    }

    async updateUserRole(userId: number, role: 'ADMIN' | 'ANNOTATOR' | 'VERIFIER') {
        const response = await api.post(`update-role/${userId}/`, { role });
        return response.data;
    }

    async getUsers(page: number = 1, perPage: number = 10, isApproved?: boolean): Promise<PaginatedResponse> {
        console.log('=== getUsers called ===');
        this.debugLocalStorage();

        const params = new URLSearchParams({
            page: page.toString(),
            per_page: perPage.toString()
        });
        if (isApproved !== undefined) {
            params.append('is_approved', isApproved.toString());
        }

        const currentUser = this.getCurrentUser();
        if (!currentUser) {
            console.error('getUsers - No valid user found');
            throw new Error('No valid user found');
        }

        try {
            const response = await api.get<PaginatedResponse>(`get-users/?${params.toString()}`);
            console.log('Users fetched successfully:', response.data);
            return response.data;
        } catch (error) {
            console.error('Error fetching users:', error);
            throw error;
        }
    }

    async refreshToken() {
        const user = localStorage.getItem('user');
        if (!user) {
            throw new Error('No user data available');
        }
        
        const userData = JSON.parse(user);
        const { refreshToken } = userData;
        
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }
        
        console.log('Manual refresh token request...');
        const response = await api.post<{ access: string }>('token/refresh/', {
            refresh: refreshToken
        });
        
        console.log('Manual refresh response:', response.data);
        
        // Update stored token
        const updatedUser = {
            ...userData,
            accessToken: response.data.access
        };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        
        return response.data;
    }

    async forgotPassword(email: string) {
        const response = await api.post('request-password-reset/', { email });
        return response.data;
    }

    async resetPassword(token: string, newPassword: string) {
        const response = await api.post('reset-password/', { token, new_password: newPassword });
        return response.data;
    }

    // Improved session validation method
    async validateSession(): Promise<boolean> {
        try {
            const user = localStorage.getItem('user');
            if (!user) {
                console.warn('validateSession - No user data found');
                return false;
            }

            const userData = JSON.parse(user);
            const { accessToken, refreshToken } = userData;
            
            if (!accessToken || !refreshToken) {
                console.warn('validateSession - Missing tokens');
                return false;
            }

            console.log('validateSession - Testing session with API call...');
            // Test the current session with a lightweight API call
            await api.get('status/');
            console.log('validateSession - Session validation successful');
            return true;
        } catch (error) {
            console.log('validateSession - Session validation failed:', error);
            
            if (
                typeof error === 'object' &&
                error !== null &&
                'response' in error &&
                (error as any).response?.status === 401
            ) {
                console.log('validateSession - Access token expired, attempting refresh...');
                try {
                    await this.refreshToken();
                    console.log('validateSession - Token refresh successful');
                    return true;
                } catch (refreshError) {
                    console.error('validateSession - Token refresh failed:', refreshError);
                    localStorage.removeItem('user');
                    return false;
                }
            }
            
            // For other errors, return false but don't clear localStorage
            // Let the user continue and handle errors via interceptors
            return false;
        }
    }

    // Add method to get current user ID for filtering
    getCurrentUserId(): number | null {
        const user = this.getCurrentUser();
        return user ? user.id : null;
    }

    async deleteUser(userId: number) {
        const response = await api.delete(`delete-user/${userId}/`);
        return response.data;
    }

    async rejectUser(userId: number) {
        const response = await api.post(`reject-user/${userId}/`);
        return response.data;
    }

    async pauseUser(userId: number) {
        const response = await api.post(`pause-user/${userId}/`);
        return response.data;
    }

    // Add method to clear corrupted session data
    clearCorruptedSession() {
        console.log('Clearing potentially corrupted session data...');
        
        try {
            const user = localStorage.getItem('user');
            if (user) {
                const userData = JSON.parse(user);
                console.log('Current user data before clearing:', userData);
            }
        } catch (error) {
            console.log('User data was corrupted:', error);
        }
        
        // Clear all auth-related data
        const authKeys = ['user', 'token', 'access_token', 'refresh_token', 'accessToken', 'refreshToken'];
        authKeys.forEach(key => {
            localStorage.removeItem(key);
        });
        
        console.log('Session data cleared. Please refresh and try logging in again.');
    }

    // Add debugging method to track what's causing the redirects
    debugSessionState() {
        console.log('=== Session Debug State ===');
        console.log('Current URL:', window.location.href);
        console.log('isRedirecting flag:', isRedirecting);
        
        const user = localStorage.getItem('user');
        console.log('localStorage user:', user ? 'exists' : 'null');
        
        if (user) {
            try {
                const userData = JSON.parse(user);
                console.log('User data valid:', !!userData);
                console.log('Has accessToken:', !!userData.accessToken);
                console.log('Has refreshToken:', !!userData.refreshToken);
            } catch (e) {
                console.log('User data corrupted:', e);
            }
        }
        
        console.log('=== End Session Debug ===');
    }
}

export const authService = new AuthService();

// Expose debug method globally for testing
(window as any).debugAuth = () => authService.debugLocalStorage();
(window as any).clearAuth = () => authService.clearCorruptedSession();
(window as any).validateAuth = () => authService.validateSession();
(window as any).debugSession = () => authService.debugSessionState();
(window as any).clearQuiet = () => authService.clearSessionQuietly();

// Debug utility - expose to window for manual use in console only
if (typeof window !== 'undefined') {
    (window as any).clearAllAuthData = () => {
        const authKeys = ['user', 'token', 'access_token', 'refresh_token', 'accessToken', 'refreshToken'];
        authKeys.forEach(key => {
            localStorage.removeItem(key);
            console.log(`Cleared: ${key}`);
        });
        console.log('All authentication data cleared. Please refresh the page.');
        window.location.reload();
    };
}