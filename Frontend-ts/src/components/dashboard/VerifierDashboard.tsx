import React from 'react';

const cards = [
  {
    icon: (
      <svg className="w-10 h-10 text-blue-500 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
    ),
    title: 'Assigned',
    desc: 'Images assigned to you and ready for verification.',
    button: 'Open Assignments',
    buttonColor: 'bg-blue-600 hover:bg-blue-700',
  },
  {
    icon: (
      <svg className="w-10 h-10 text-green-500 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2l4-4" /></svg>
    ),
    title: 'Annotated',
    desc: 'Images you have successfully verified.',
    button: 'View Annotated',
    buttonColor: 'bg-green-500 hover:bg-green-600',
  },
  {
    icon: (
      <svg className="w-10 h-10 text-orange-500 mx-auto" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3" /></svg>
    ),
    title: 'Pending',
    desc: 'Images that require further action or are pending review.',
    button: 'Open Pending',
    buttonColor: 'bg-orange-500 hover:bg-orange-600',
  },
];

const VerifierDashboard: React.FC = () => (
  <div className="min-h-screen bg-gray-100 flex flex-col items-center p-6">
    <div className="w-full max-w-5xl mx-auto">
      <div className="bg-white rounded-2xl shadow p-6 mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Verifier Dashboard</h1>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {cards.map((card, idx) => (
          <div key={idx} className="bg-white rounded-xl shadow-md p-6 flex flex-col items-center">
            {card.icon}
            <h2 className="mt-4 text-lg font-semibold text-gray-800">{card.title}</h2>
            <p className="mt-2 text-gray-500 text-center">{card.desc}</p>
            <button className={`mt-6 w-full py-2 rounded-lg text-white font-medium ${card.buttonColor}`}>{card.button}</button>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default VerifierDashboard; 