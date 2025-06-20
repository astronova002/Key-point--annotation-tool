import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import axios from 'axios';
import { authService } from '../services/authService';

interface User {
    id: number;
    username: string;
    email: string;
    role: 'ADMIN' | 'ANNOTATOR' | 'VERIFIER';
    accessToken?: string;
    refreshToken?: string;
}

interface LoginResponse {
    user: User;
    token: {
        access: string;
        refresh: string;
    };
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    error: string | null;
    isAuthenticated: boolean;
    login: (username: string, password: string) => Promise<User>;
    register: (username: string, email: string, password: string, role: 'ADMIN' | 'ANNOTATOR' | 'VERIFIER') => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isLoggingIn, setIsLoggingIn] = useState(false);

    // Computed property for authentication status
    const isAuthenticated = !!user;

    // Check for existing session on mount
    useEffect(() => {
        const checkSession = async () => {
            try {
                setLoading(true);
                
                // Get user data from authService instead of directly from localStorage
                const userData = authService.getCurrentUser();
                
                if (userData) {
                    console.log('AuthContext: Found valid user data:', userData);
                    setUser(userData);
                    
                    // Optionally validate session in background (don't block UI)
                    authService.validateSession().catch(error => {
                        console.warn('Background session validation failed:', error);
                        // Don't clear user immediately - let interceptors handle it
                    });
                } else {
                    console.log('AuthContext: No valid user data found');
                    setUser(null);
                }
                
            } catch (err) {
                console.error('AuthContext: Error during session check:', err);
                setUser(null);
            } finally {
                setLoading(false);
                console.log('AuthContext: Session check complete');
            }
        };

        checkSession();
    }, []);

    const login = async (username: string, password: string): Promise<User> => {
        if (isLoggingIn) {
            return Promise.reject(new Error('Login already in progress'));
        }
        
        try {
            setIsLoggingIn(true);
            setLoading(true);
            setError(null);
            
            const response = await authService.login(username, password);
            console.log('Login response from authService:', response);
            
            // Handle the response properly - the response should be the user data with tokens
            if (response && typeof response === 'object') {
                let contextUser: User;
                
                // Check if response has the direct format from backend
                if ('accessToken' in response && 'refreshToken' in response) {
                    contextUser = {
                        id: response.id,
                        username: response.username,
                        email: response.email,
                        role: response.role as 'ADMIN' | 'ANNOTATOR' | 'VERIFIER',
                        accessToken: typeof response.accessToken === 'string' ? response.accessToken : undefined,
                        refreshToken: typeof response.refreshToken === 'string' ? response.refreshToken : undefined
                    };
                } else {
                    throw new Error('Invalid response format from login');
                }
                
                console.log('Setting user in context:', contextUser);
                setUser(contextUser);
                return contextUser;
            } else {
                throw new Error('Invalid response from login service');
            }
        } catch (err) {
            console.error('Login failed:', err);
            setError(err instanceof Error ? err.message : 'Login failed');
            throw err;
        } finally {
            setLoading(false);
            setLoading(false);
        }
    };

    const register = async (username: string, email: string, password: string, role: 'ADMIN' | 'ANNOTATOR' | 'VERIFIER') => {
        try {
            setLoading(true);
            setError(null);
            await authService.register({ username, email, password, role });
        } catch (err) {
            setError('Registration failed. Please try again.');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        console.log('AuthContext: Logging out user');
        setUser(null);
        localStorage.removeItem('user');
        
        // Call authService logout but don't wait for it
        authService.logout().catch(error => {
            console.warn('Logout API call failed:', error);
        });
    };

    return (
        <AuthContext.Provider value={{ user, loading, error, isAuthenticated, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export default AuthContext;