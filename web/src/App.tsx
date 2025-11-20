import { useState, useEffect, useRef } from 'react';
import { Moon, Sun, UserCircle2 } from 'lucide-react';
import { useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import AdminRSDashboard from './components/AdminRSDashboard';
import AdminMetaDashboard from './components/AdminMetaDashboard';
import { apiService } from './lib/api';

function App() {
  const { user, isLoading: authLoading, isAuthenticated, logout } = useAuth();
  const [isDark, setIsDark] = useState(true);
  const [aiUsage, setAiUsage] = useState<{ used: number; remaining: number; limit: number } | null>(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileRef = useRef<HTMLDivElement | null>(null);

  const loadAIUsage = async () => {
    try {
      const response = await apiService.getAIUsageStatus();
      if (response.success) {
        setAiUsage(response.data);
      }
    } catch (error) {
      console.error('Failed to load AI usage status:', error);
    }
  };

  // Load AI usage once user is authenticated
  useEffect(() => {
    if (!isAuthenticated) return;
    void loadAIUsage();
  }, [isAuthenticated]);

  // Close profile menu when clicking outside profile area
  useEffect(() => {
    if (!showProfileMenu) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (!profileRef.current) return;
      if (!profileRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showProfileMenu]);

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
      return <AdminRSDashboard isDark={isDark} user={user} />;
    } else {
      // Default dashboard for regular users (if any)
      return <AdminRSDashboard isDark={isDark} user={user} />;
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

      <div className="relative z-20 h-full flex flex-col">
        <header
          className={`${
            isDark
              ? 'bg-gradient-to-r from-slate-800/80 to-slate-900/80 border-b border-cyan-500/20'
              : 'bg-gradient-to-r from-blue-600/90 to-blue-800/90 border-b border-blue-400/30'
          } backdrop-blur-xl shadow-2xl flex-shrink-0 relative z-30`}
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

            <div className="relative flex items-center gap-3" ref={profileRef}>
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
                onClick={() =>
                  setShowProfileMenu((prev) => {
                    const next = !prev;
                    if (!prev) {
                      void loadAIUsage();
                    }
                    return next;
                  })
                }
                className={`p-2 rounded-full border flex items-center justify-center ${
                  isDark
                    ? 'border-cyan-500/40 bg-slate-900/60 text-cyan-300 hover:bg-slate-800'
                    : 'border-blue-200 bg-blue-600/80 text-white hover:bg-blue-500'
                } transition-all duration-300 hover:scale-110 active:scale-95`}
                title="Profil"
              >
                <UserCircle2 className="w-5 h-5" />
              </button>

              {showProfileMenu && (
                <div
                  className={`absolute right-0 top-14 w-72 rounded-xl shadow-2xl border backdrop-blur-xl z-50 ${
                    isDark
                      ? 'bg-slate-900/95 border-cyan-500/30'
                      : 'bg-white/95 border-blue-100'
                  }`}
                >
                  <div className="px-4 py-3 border-b border-white/5 flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold ${
                        isDark ? 'bg-cyan-500/20 text-cyan-200' : 'bg-blue-600 text-white'
                      }`}
                    >
                      {(user?.full_name || 'U')
                        .split(' ')
                        .filter(Boolean)
                        .slice(0, 2)
                        .map((p) => p.charAt(0))
                        .join('')
                        .toUpperCase()}
                    </div>
                    <div>
                      <div
                        className={`text-sm font-semibold ${
                          isDark ? 'text-slate-100' : 'text-blue-900'
                        }`}
                      >
                        {user?.full_name}
                      </div>
                      <div
                        className={`text-xs ${
                          isDark ? 'text-slate-400' : 'text-blue-500'
                        }`}
                      >
                        {user?.email}
                      </div>
                    </div>
                  </div>

                  <div className="px-4 py-3 text-xs">
                    <div
                      className={`mb-2 flex items-center justify-between ${
                        isDark ? 'text-slate-300' : 'text-blue-800'
                      }`}
                    >
                      <span>Penggunaan AI Hari Ini</span>
                      {aiUsage && (
                        <span
                          className={`font-semibold ${
                            aiUsage.remaining === 0
                              ? 'text-red-400'
                              : aiUsage.remaining < 10
                              ? 'text-yellow-500'
                              : isDark
                              ? 'text-cyan-300'
                              : 'text-blue-700'
                          }`}
                        >
                          {aiUsage.used}/{aiUsage.limit}
                        </span>
                      )}
                    </div>
                    {aiUsage ? (
                      <>
                        <div
                          className={`w-full h-2 rounded-full mb-1 ${
                            isDark ? 'bg-slate-700' : 'bg-blue-100'
                          }`}
                        >
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              aiUsage.remaining === 0
                                ? 'bg-red-500'
                                : aiUsage.remaining < 10
                                ? 'bg-yellow-500'
                                : 'bg-gradient-to-r from-cyan-500 to-blue-500'
                            }`}
                            style={{ width: `${(aiUsage.used / aiUsage.limit) * 100}%` }}
                          />
                        </div>
                        <div
                          className={`${
                            isDark ? 'text-slate-400' : 'text-gray-600'
                          }`}
                        >
                          Sisa {aiUsage.remaining} permintaan hari ini
                        </div>
                      </>
                    ) : (
                      <div
                        className={`${
                          isDark ? 'text-slate-500' : 'text-gray-500'
                        }`}
                      >
                        Memuat status penggunaan AI...
                      </div>
                    )}
                  </div>
                  <div className="px-4 py-3 border-t border-white/5 flex justify-end">
                    <button
                      onClick={logout}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        isDark
                          ? 'bg-red-500/20 hover:bg-red-500/30 text-red-300'
                          : 'bg-red-500/10 hover:bg-red-500/20 text-red-600'
                      }`}
                    >
                      Logout
                    </button>
                  </div>
                </div>
              )}
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
