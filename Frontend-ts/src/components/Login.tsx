import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link, useLocation } from 'react-router-dom';

const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        
        try {
            console.log('Starting login process...');
            const userData = await login(username, password);
            console.log('Login response:', userData);
            
            if (!userData) {
                throw new Error('No user data received from login');
            }

            console.log('User data:', userData);

            // Check if user data is valid and has role
            if (userData && userData.role) {
                console.log('User role:', userData.role);
                
                // Navigate based on role
                switch (userData.role) {
                    case 'ADMIN':
                        console.log('Navigating to /superuser');
                        navigate('/superuser', { replace: true });
                        break;
                    case 'ANNOTATOR':
                        console.log('Navigating to /annotator');
                        navigate('/annotator', { replace: true });
                        break;
                    case 'VERIFIER':
                        console.log('Navigating to /verifier');
                        navigate('/verifier', { replace: true });
                        break;
                    default:
                        console.log('Unknown role, navigating to root');
                        navigate('/', { replace: true });
                }
            } else {
                console.error('Invalid user data or missing role:', userData);
                setError('Invalid user data received. Please try again.');
            }
        } catch (err: any) {
            console.error('Login error:', err);
            setError(err.response?.data?.error || err.message || 'Failed to login. Please check your credentials.');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        Sign in to your account
                    </h2>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    {error && (
                        <div className="rounded-md bg-red-50 p-4">
                            <div className="text-sm text-red-700">{error}</div>
                        </div>
                    )}
                    <div className="rounded-md shadow-sm -space-y-px">
                        <div>
                            <label htmlFor="username" className="sr-only">
                                Username
                            </label>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="Username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="sr-only">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                            Sign in
                        </button>
                    </div>
                </form>
                <div className="text-sm text-center">
                    <Link to="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
                        Don't have an account? Register
                    </Link>
                    <br />
                    <Link to="/forgot-password" className="font-medium text-indigo-600 hover:text-indigo-500">
                        Forgot your password?
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default Login;