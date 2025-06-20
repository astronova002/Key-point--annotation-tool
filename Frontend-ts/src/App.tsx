import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/Login';
import Register from './components/Register';
import PrivateRoute from './components/PrivateRoute';
import AnnotatorDashboard from './components/dashboard/AnnotatorDashboard';
import VerifierDashboard from './components/VerifierDashboard';
import SuperUserDashboard from './components/dashboard/SuperUserDashboard';
import UserManagement from './components/dashboard/UserManagement';
import Unauthorized from './components/Unauthorized';
import LandingPage from './components/landing/LandingPage';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import AuthDebugger from './components/AuthDebugger';
import ImageUploadPage from './components/pages/ImageUploadPage';
import BatchProcessorPage from './components/pages/BatchProcessorPage';
// import BulkAssign from './components/BulkAssign';
import './App.css';

const App: React.FC = () => {
    return (
        <AuthProvider>
            <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                <Routes>
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/forgot-password" element={<ForgotPassword />} />
                    <Route path="/reset-password/:token" element={<ResetPassword />} />
                    <Route path="/unauthorized" element={<Unauthorized />} />
                    <Route path="/debug" element={<AuthDebugger />} />
                    <Route
                        path="/superuser"
                        element={
                            <PrivateRoute allowedRoles={['ADMIN']}>
                                <SuperUserDashboard />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/user-management"
                        element={
                            <PrivateRoute allowedRoles={['ADMIN']}>
                                <UserManagement />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/upload-images"
                        element={
                            <PrivateRoute allowedRoles={['ADMIN']}>
                                <ImageUploadPage />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/batch-processor"
                        element={
                            <PrivateRoute allowedRoles={['ADMIN']}>
                                <BatchProcessorPage />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/annotator"
                        element={
                            <PrivateRoute allowedRoles={['ANNOTATOR']}>
                                <AnnotatorDashboard />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/verifier"
                        element={
                            <PrivateRoute allowedRoles={['VERIFIER']}>
                                <VerifierDashboard />
                            </PrivateRoute>
                        }
                    />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </Router>
        </AuthProvider>
    );
};

export default App;
