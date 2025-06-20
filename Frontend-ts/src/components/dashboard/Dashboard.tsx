import { Navigate } from 'react-router-dom';
import SuperUserDashboard from './SuperUserDashboard';
import AnnotatorDashboard from './AnnotatorDashboard';
import VerifierDashboard from './VerifierDashboard';

const Dashboard = () => {
  // TODO: Replace this with actual user role from your auth context/state
  type UserRole = 'superuser' | 'annotator' | 'verifier';
  const userRole = 'superuser' as UserRole; // This should come from your auth state

  switch (userRole) {
    case 'superuser':
      return <SuperUserDashboard />;
    case 'annotator':
      return <AnnotatorDashboard />;
    case 'verifier':
      return <VerifierDashboard />;
    default:
      return <Navigate to="/login" replace />;
  }
};

export default Dashboard; 