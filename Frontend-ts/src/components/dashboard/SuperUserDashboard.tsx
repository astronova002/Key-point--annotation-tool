import React from 'react';
import { useNavigate } from 'react-router-dom';
import Logout from '../Logout';

const cards = [
  {
    icon: (
      <svg className="w-10 h-10 text-blue-400 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
    ),
    title: 'Upload Images',
    desc: 'Upload multiple images for batch processing.',
    button: 'Go to Upload',
    color: 'bg-blue-600',
    buttonColor: 'bg-blue-600 hover:bg-blue-700',
    path: '/upload-images'
  },
  {
    icon: (
      <svg className="w-10 h-10 text-indigo-400 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
    ),
    title: 'YOLO Batch Processor',
    desc: 'Process uploaded batches with 26-keypoint YOLO model.',
    button: 'Process Batches',
    color: 'bg-indigo-600',
    buttonColor: 'bg-indigo-600 hover:bg-indigo-700',
    path: '/batch-processor'
  },
  {
    icon: (
      <svg className="w-10 h-10 text-orange-400 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2a4 4 0 014-4h4m0 0V7a4 4 0 00-4-4H7a4 4 0 00-4 4v10a4 4 0 004 4h4" /></svg>
    ),
    title: 'Assign Images',
    desc: 'Assign images to annotators for processing.',
    button: 'Go to Assign',
    color: 'bg-orange-500',
    buttonColor: 'bg-orange-500 hover:bg-orange-600',
    path: '/assign'
  },
  {
    icon: (
      <svg className="w-10 h-10 text-green-400 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 11c0-1.104.896-2 2-2s2 .896 2 2-.896 2-2 2-2-.896-2-2zm0 0V7m0 4v4m0 0a4 4 0 01-4-4V7a4 4 0 014-4h4a4 4 0 014 4v4a4 4 0 01-4 4h-4z" /></svg>
    ),
    title: 'Users Approval and Roles',  
    desc: 'Manage user roles and permissions.',
    button: 'Go to Users',
    color: 'bg-green-500',
    buttonColor: 'bg-green-500 hover:bg-green-600',
    path: '/user-management'
  },
  {
    icon: (
      <svg className="w-10 h-10 text-pink-400 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
    ),
    title: 'Verified/Rejected Images',
    desc: 'Review and manage image statuses.',
    button: 'View Statuses',
    color: 'bg-pink-500',
    buttonColor: 'bg-pink-500 hover:bg-pink-600',
    path: '/status'
  },
  {
    icon: (
      <svg className="w-10 h-10 text-purple-400 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2h5" /></svg>
    ),
    title: 'View Assignments',
    desc: 'View assigned annotators and their images.',
    button: 'View Assignments',
    color: 'bg-purple-500',
    buttonColor: 'bg-purple-500 hover:bg-purple-600',
    path: '/assignments'
  }
];

const SuperUserDashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-6">
      {/* Floating Top Bar */}
      <header className="sticky top-0 z-50 w-full bg-white/80 backdrop-blur border-b border-black/5 rounded-b-2xl shadow-sm mb-8 flex items-center justify-between px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-800">Super User Dashboard</h1>
        <Logout />
      </header>
      <div className="w-full max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {cards.map((card, idx) => (
            <div
              key={idx}
              className="dashboard-card bg-white rounded-xl shadow-md p-6 flex flex-col items-center transition-transform hover:-translate-y-1 hover:shadow-lg overflow-hidden"
            >
              {card.icon}
              <h2 className="mt-4 text-lg font-semibold text-gray-800">{card.title}</h2>
              <p className="mt-2 text-gray-500 text-center">{card.desc}</p>
              <button 
                onClick={() => navigate(card.path)}
                className={`mt-6 w-full py-2 rounded-lg text-white font-medium ${card.buttonColor}`}
              >
                {card.button}
              </button>
            </div>
          ))}
        </div>
      </div>
      <style>{`
        .dashboard-card { box-shadow: 0 8px 16px rgba(0,0,0,0.05); border-radius: 16px; transition: transform 0.3s, box-shadow 0.3s; }
        .dashboard-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }
      `}</style>
    </div>
  );
};

export default SuperUserDashboard;