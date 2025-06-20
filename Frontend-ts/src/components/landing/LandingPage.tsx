import React from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage: React.FC = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
            {/* Logo in top left with box */}
            <div className="absolute top-4 left-4">
                <div className="flex items-center space-x-2 bg-white p-2 rounded-lg shadow-md">
                    <span className="text-2xl font-bold text-blue-600">GMA</span>
                    <span className="text-sm text-gray-600">Keypoint Tool</span>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col items-center justify-center min-h-screen text-center">
                    {/* Main Title */}
                    <div className="mb-8">
                        <h1 className="text-5xl font-extrabold text-gray-900 mb-4">
                            GMA
                        </h1>
                        <h2 className="text-3xl font-semibold text-gray-700 mb-2">  
                            General Movement Assessment
                        </h2>
                        <p className="text-xl text-gray-600">
                            Keypoint Annotation Tool
                        </p>
                    </div>

                    {/* Description */}
                    <div className="max-w-2xl mb-12">
                        <p className="text-lg text-gray-600">
                            A powerful tool for annotating keypoints in general movement assessment videos.
                            Streamline your research and analysis with our intuitive interface.
                        </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-col sm:flex-row gap-4">
                        <button
                            onClick={() => navigate('/login')}
                            className="px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200"
                        >
                            Login
                        </button>
                        <button
                            onClick={() => navigate('/register')}
                            className="px-8 py-3 text-lg font-medium text-blue-600 bg-white border-2 border-blue-600 rounded-lg hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200"
                        >
                            Sign Up
                        </button>
                    </div>

                    {/* Features Section */}
                    <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="p-6 bg-white rounded-xl shadow-md">
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">Easy Annotation</h3>
                            <p className="text-gray-600">Intuitive interface for quick and accurate keypoint annotation</p>
                        </div>
                        <div className="p-6 bg-white rounded-xl shadow-md">
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">Video Analysis</h3>
                            <p className="text-gray-600">Frame-by-frame analysis with precise control</p>
                        </div>
                        <div className="p-6 bg-white rounded-xl shadow-md">
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">Data Export</h3>
                            <p className="text-gray-600">Export your annotations in various formats for analysis</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LandingPage; 