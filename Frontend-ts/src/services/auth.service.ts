import api from './api';

interface LoginCredentials {
    email: string;
    password: string;
}

interface SignupCredentials {
    name: string;
    email: string;
    password: string;
}

interface AuthResponse {
    token: string;
    user: {
        id: string;
        email: string;
        name: string;
    };
}

export const authService = {
    async login(credentials: LoginCredentials): Promise<AuthResponse> {
        console.log('Sending login request:', credentials);
        try {
            const response = await api.post<AuthResponse>('/auth/login', credentials);
            console.log('Login response:', response.data);
            const { token, user } = response.data;
            
            // Store token in localStorage
            localStorage.setItem('token', token);
            
            return response.data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    async signup(credentials: SignupCredentials): Promise<AuthResponse> {
        console.log('Sending signup request:', credentials);
        try {
            const response = await api.post<AuthResponse>('/auth/signup', credentials);
            console.log('Signup response:', response.data);
            const { token, user } = response.data;
            
            // Store token in localStorage
            localStorage.setItem('token', token);
            
            return response.data;
        } catch (error) {
            console.error('Signup error:', error);
            throw error;
        }
    },

    logout(): void {
        localStorage.removeItem('token');
        window.location.href = '/login';
    },

    isAuthenticated(): boolean {
        return !!localStorage.getItem('token');
    }
}; 