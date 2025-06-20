import React from 'react';
import { useNavigate } from 'react-router-dom';
import BulkImageUpload from '../upload/BulkImageUpload';
import { useAuth } from '../../contexts/AuthContext';
import Logout from '../Logout';

const ImageUploadPage: React.FC = () => {
    const { user } = useAuth();
    const navigate = useNavigate();

    const handleBackToDashboard = () => {
        navigate('/superuser');
    };

    return (
        <div className="min-h-screen bg-gray-100 flex flex-col items-center p-6">
            {/* Floating Top Bar - Consistent with SuperUserDashboard */}
            <header className="sticky top-0 z-50 w-full bg-white/80 backdrop-blur border-b border-black/5 rounded-b-2xl shadow-sm mb-8 flex items-center justify-between px-6 py-4">
                <div className="flex items-center gap-4">
                    {/* Back Button */}
                    <button
                        onClick={handleBackToDashboard}
                        className="p-2 rounded-full hover:bg-gray-200 transition-colors"
                        title="Back to Dashboard"
                    >
                        <svg 
                            className="w-5 h-5 text-gray-600" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                        >
                            <path 
                                strokeLinecap="round" 
                                strokeLinejoin="round" 
                                strokeWidth="2" 
                                d="M15 19l-7-7 7-7" 
                            />
                        </svg>
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">Image Upload</h1>
                        <p className="text-sm text-gray-600">Upload images for annotation processing</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600">
                        Welcome, {user?.username}
                    </span>
                    <Logout />
                </div>
            </header>

            {/* Main Content - Consistent with dashboard layout */}
            <div className="w-full max-w-6xl mx-auto">
                <div className="dashboard-card bg-white rounded-xl shadow-md p-8 transition-transform hover:-translate-y-1 hover:shadow-lg">
                    {/* Upload Section Header */}
                    <div className="mb-6 text-center">
                        <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                            <svg 
                                className="w-8 h-8 text-blue-600" 
                                fill="none" 
                                stroke="currentColor" 
                                strokeWidth="2" 
                                viewBox="0 0 24 24"
                            >
                                <path 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round" 
                                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
                                />
                            </svg>
                        </div>
                        <h2 className="text-xl font-semibold text-gray-800 mb-2">
                            Bulk Image Upload
                        </h2>
                        <p className="text-gray-600">
                            Select and upload multiple images for automatic YOLO processing and annotation workflow
                        </p>
                    </div>

                    {/* Upload Component */}
                    <BulkImageUpload />
                </div>
            </div>

            {/* Consistent styling with other dashboards */}
            <style>{`
                .dashboard-card { 
                    box-shadow: 0 8px 16px rgba(0,0,0,0.05); 
                    border-radius: 16px; 
                    transition: transform 0.3s, box-shadow 0.3s; 
                }
                .dashboard-card:hover { 
                    transform: translateY(-4px); 
                    box-shadow: 0 12px 24px rgba(0,0,0,0.08); 
                }
            `}</style>
        </div>
    );
};

export default ImageUploadPage;