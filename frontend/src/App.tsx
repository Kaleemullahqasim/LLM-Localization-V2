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

  const getRoleColor = () => {
    switch (user?.role) {
      case 'admin': return '#8b5cf6';
      case 'test-taker': return '#3b82f6';
      case 'evaluator': return '#10b981';
      default: return '#667eea';
    }
  };

  const getRoleLabel = () => {
    switch (user?.role) {
      case 'admin': return 'Administrator';
      case 'test-taker': return 'Test Taker';
      case 'evaluator': return 'Evaluator';
      default: return user?.role;
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f8fafc',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        background: 'white',
        borderBottom: '1px solid #e2e8f0',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)'
      }}>
        <div style={{
          maxWidth: '1600px',
          margin: '0 auto',
          padding: '1.25rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div>
              <h1 style={{
                fontSize: '1.5rem',
                fontWeight: '700',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0
              }}>
                Translation QA System
              </h1>
              <p style={{
                fontSize: '0.8125rem',
                color: '#64748b',
                margin: '0.25rem 0 0 0'
              }}>
                Automated Quality Assurance Platform
              </p>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{
                fontSize: '0.9375rem',
                fontWeight: '600',
                color: '#1e293b',
                marginBottom: '0.25rem'
              }}>
                {user?.name}
              </div>
              <div style={{
                display: 'inline-block',
                padding: '0.25rem 0.75rem',
                background: `${getRoleColor()}15`,
                color: getRoleColor(),
                borderRadius: '1rem',
                fontSize: '0.75rem',
                fontWeight: '600',
                textTransform: 'uppercase',
                letterSpacing: '0.025em'
              }}>
                {getRoleLabel()}
              </div>
            </div>
            <button
              onClick={logout}
              style={{
                padding: '0.625rem 1.25rem',
                background: 'white',
                color: '#64748b',
                border: '1px solid #e2e8f0',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                fontWeight: '500',
                fontSize: '0.875rem',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#f8fafc';
                e.currentTarget.style.borderColor = '#cbd5e1';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.borderColor = '#e2e8f0';
              }}
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div>
        {user?.role === 'admin' && <AdminDashboard />}
        {user?.role === 'test-taker' && <TestTakerDashboard />}
        {user?.role === 'evaluator' && <EvaluatorDashboard />}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
