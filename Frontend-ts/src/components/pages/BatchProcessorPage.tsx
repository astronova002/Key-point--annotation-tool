import React from 'react';
import { useNavigate } from 'react-router-dom';
import BatchProcessor from '../upload/BatchProcessor';
import { useAuth } from '../../contexts/AuthContext';
import Logout from '../Logout';

const BatchProcessorPage: React.FC = () => {
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
                        <h1 className="text-2xl font-bold text-gray-800">YOLO Batch Processor</h1>
                        <p className="text-sm text-gray-600">Process uploaded batches with 26-keypoint YOLO model</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600">
                        Welcome, {user?.username}
                    </span>
                    <Logout />
                </div>
            </header>

            {/* Main Content */}
            <div className="w-full max-w-6xl">
                <BatchProcessor />
            </div>
        </div>
    );
};

export default BatchProcessorPage;
