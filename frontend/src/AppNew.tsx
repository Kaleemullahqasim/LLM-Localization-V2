import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import AdminDashboard from './components/AdminDashboard';
import TestTakerDashboard from './components/TestTakerDashboard';
import EvaluatorDashboard from './components/EvaluatorDashboard';

function AppContent() {
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Login />;
  }

  // Header for all authenticated users
  const Header = () => (
    <div style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      padding: '1rem 2rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
    }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: 0 }}>
          Translation QA System
        </h1>
        <p style={{ fontSize: '0.875rem', opacity: 0.9, margin: '0.25rem 0 0 0' }}>
          {user?.name} ({user?.role})
        </p>
      </div>
      <button
        onClick={logout}
        style={{
          padding: '0.5rem 1.5rem',
          background: 'rgba(255,255,255,0.2)',
          color: 'white',
          border: '1px solid rgba(255,255,255,0.3)',
          borderRadius: '0.5rem',
          cursor: 'pointer',
          fontWeight: '600'
        }}
      >
        Logout
      </button>
    </div>
  );

  return (
    <div>
      <Header />
      <div style={{ minHeight: 'calc(100vh - 80px)' }}>
        {user?.role === 'admin' && <AdminDashboard />}
        {user?.role === 'test-taker' && <TestTakerDashboard />}
        {user?.role === 'evaluator' && <EvaluatorDashboard />}
      </div>
    </div>
  );
}

export default function AppNew() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

