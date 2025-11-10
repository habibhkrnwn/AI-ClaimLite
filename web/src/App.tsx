import { useState } from 'react';
import { LogOut, Moon, Sun } from 'lucide-react';
import { useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import AdminRSDashboard from './components/AdminRSDashboard';
import AdminMetaDashboard from './components/AdminMetaDashboard';

function App() {
  const { user, isLoading: authLoading, isAuthenticated, logout } = useAuth();
  const [isDark, setIsDark] = useState(true);

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-cyan-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage isDark={isDark} />;
  }

  // Determine which dashboard to show based on user role
  const renderDashboard = () => {
    if (user?.role === 'Admin Meta') {
      return <AdminMetaDashboard isDark={isDark} />;
    } else if (user?.role === 'Admin RS') {
      return <AdminRSDashboard isDark={isDark} />;
    } else {
      // Default dashboard for regular users (if any)
      return <AdminRSDashboard isDark={isDark} />;
    }
  };

  return (
    <div
      className={`fixed inset-0 transition-all duration-500 ${
        isDark
          ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900'
          : 'bg-gradient-to-br from-blue-50 via-white to-blue-50'
      } overflow-hidden`}
    >
      <div
        className={`absolute inset-0 opacity-20 ${
          isDark ? 'bg-grid-cyan' : 'bg-grid-blue'
        }`}
        style={{
          backgroundImage: `radial-gradient(circle, ${isDark ? '#06b6d4' : '#3b82f6'} 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />

      <div className="relative z-10 h-full flex flex-col">
        <header
          className={`${
            isDark
              ? 'bg-gradient-to-r from-slate-800/80 to-slate-900/80 border-b border-cyan-500/20'
              : 'bg-gradient-to-r from-blue-600/90 to-blue-800/90 border-b border-blue-400/30'
          } backdrop-blur-xl shadow-2xl flex-shrink-0`}
        >
          <div className="px-6 py-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div>
                <h1
                  className={`text-2xl font-bold ${
                    isDark
                      ? 'bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent'
                      : 'text-white'
                  }`}
                >
                  AI-CLAIM Lite
                </h1>
                <p
                  className={`text-sm ${
                    isDark ? 'text-slate-400' : 'text-blue-100'
                  }`}
                >
                  {user?.role || 'User'} Dashboard
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-blue-100'}`}>
                {user?.full_name}
              </div>
              <button
                onClick={() => setIsDark(!isDark)}
                className={`p-3 rounded-lg ${
                  isDark
                    ? 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400'
                    : 'bg-white/20 hover:bg-white/30 text-white'
                } backdrop-blur-sm transition-all duration-300 hover:scale-110 active:scale-95`}
                title="Toggle Theme"
              >
                {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <button
                onClick={logout}
                className={`p-3 rounded-lg ${
                  isDark
                    ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
                    : 'bg-red-500/20 hover:bg-red-500/30 text-red-600'
                } backdrop-blur-sm transition-all duration-300 hover:scale-110 active:scale-95`}
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-hidden">
          <div className="px-6 py-6 h-full">
            {renderDashboard()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
