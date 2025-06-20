import React from 'react';
import Logout from '../Logout';

const BellIcon = () => (
  <svg className="text-gray-600" fill="none" height="24" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" width="24">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);

const Avatar = () => (
  <div
    className="bg-center bg-no-repeat aspect-square bg-cover rounded-full w-10 h-10 border-2 border-white shadow-sm"
    style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuCUijGnZE91KOo7mVDUlTrTI8j7jd06N8xq7-GWxzweSDYEIq-TZVsLnsTuYizVxOfQWFdhHdS_CxKWE11Ktb34S1p4KWL0ZPHOKZa_cvIzxPO8qmfNl8PS1ICUNG-FT-L7eFFvsO9kfG6LuoOeoQB609RIZCjjzFn7phKTnTYk-BqOLDuiwxn3mOS_WK-47Ayy1-eutn1BT1l3nGIBCndTNw29I1zF4DxtSLMuPnxFh9wNikGun7po7gl-lwdtBtm8NaFn0oUPTjFt")' }}
  />
);

const cards = [
  {
    icon: (
      <div className="apple-icon-wrapper flex items-center justify-center w-11 h-11 rounded-full mr-3" style={{ backgroundColor: '#007AFF' }}>
        <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white" xmlns="http://www.w3.org/2000/svg">
          <path d="M19.50001,3.69997H4.5C3.39543,3.69997,2.5,4.5954,2.5,5.69997V16.3C2.5,17.40457,3.39543,18.3,4.5,18.3h15.00001C20.60458,18.3,21.5,17.40457,21.5,16.3V5.69997C21.5,4.5954,20.60458,3.69997,19.50001,3.69997ZM4,5.69997C4,5.14769,4.44772,4.69997,5,4.69997H19C19.55229,4.69997,20,5.14769,20,5.69997V7.3H4V5.69997ZM4,16.3V8.8H20v7.5c0,.55228-.44772,1-1,1H5C4.44772,17.3,4,16.85228,4,16.3ZM6,11.14997c0-.41421.33579-.75.75-.75H10c.41421,0,.75.33579.75.75s-.33579.75-.75.75H6.75C6.33579,11.89997,6,11.56418,6,11.14997Zm0,3c0-.41421.33579-.75.75-.75H8c.41421,0,.75.33579.75.75s-.33579.75-.75.75H6.75C6.33579,14.89997,6,14.56418,6,14.14997Z"></path>
        </svg>
      </div>
    ),
    title: 'Assigned',
    desc: 'Images ready for annotation.',
    button: 'Open List',
  },
  {
    icon: (
      <div className="apple-icon-wrapper flex items-center justify-center w-11 h-11 rounded-full mr-3" style={{ backgroundColor: '#34C759' }}>
        <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white" xmlns="http://www.w3.org/2000/svg">
          <path d="M8.707 14.293a1 1 0 0 1 0-1.414l5-5a1 1 0 0 1 1.414 1.414L9.414 14l5.293 5.293a1 1 0 0 1-1.414 1.414l-5-5zm6.586-9.586a2 2 0 0 0-2.828 0L4 13.172V17a2 2 0 0 0 2 2h3.828l8.464-8.464a2 2 0 0 0 0-2.828zM7.586 17H6v-1.586L13.293 8.121l1.586 1.586L7.586 17z"></path>
        </svg>
      </div>
    ),
    title: 'Annotated',
    desc: 'Completed and reviewed images.',
    button: 'View Table',
  },
  {
    icon: (
      <div className="apple-icon-wrapper flex items-center justify-center w-11 h-11 rounded-full mr-3" style={{ backgroundColor: '#FF9500' }}>
        <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2C6.486 2 2 6.486 2 12s4.486 10 10 10 10-4.486 10-10S17.514 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8zm-1-13h2v5h-2zm0 6h2v2h-2z"></path>
        </svg>
      </div>
    ),
    title: 'Pending',
    desc: 'Images awaiting review or action.',
    button: 'Open Queue',
  },
];

const ArrowIcon = () => (
  <svg className="ml-2" fill="currentColor" height="16" viewBox="0 0 16 16" width="16" xmlns="http://www.w3.org/2000/svg">
    <path d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z" fillRule="evenodd"></path>
  </svg>
);

const AnnotatorDashboard: React.FC = () => (
  <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-[#f8f9fa]">
    <div className="flex h-full grow flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 bg-white/80 backdrop-blur border-b border-black/5">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-gray-800">Annotator Dashboard</h1>
        </div>
        <div className="flex items-center gap-4">
          <button className="p-2 rounded-full hover:bg-gray-200 transition-colors">
            <BellIcon />
          </button>
          <Logout />
        </div>
      </header>
      {/* Main */}
      <main className="flex-1 p-6 lg:p-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {cards.map((card, idx) => (
            <div key={idx} className="dashboard-card flex flex-col p-6 bg-white rounded-2xl shadow-md transition-transform hover:-translate-y-1 hover:shadow-lg overflow-hidden">
              <div className="flex items-center mb-4">
                {card.icon}
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">{card.title}</h3>
                  <p className="text-sm text-gray-500">{card.desc}</p>
                </div>
              </div>
              <div className="mt-auto">
                <button className="action-button w-full flex items-center justify-center bg-[#F0F0F5] text-black rounded-full py-2 px-5 font-semibold text-[15px] transition-colors hover:bg-[#E5E5EB]">
                  {card.button}
                  <ArrowIcon />
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
    {/* Custom styles for dashboard-card and action-button */}
    <style>{`
      .dashboard-card { box-shadow: 0 8px 16px rgba(0,0,0,0.05); border-radius: 16px; transition: transform 0.3s, box-shadow 0.3s; }
      .dashboard-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); }
      .action-button { background-color: #F0F0F5; color: #000; border-radius: 9999px; font-weight: 600; font-size: 15px; }
      .action-button:hover { background-color: #E5E5EB; }
    `}</style>
  </div>
);

export default AnnotatorDashboard; 