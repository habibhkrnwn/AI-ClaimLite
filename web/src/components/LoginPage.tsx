import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, Mail, Lock, Loader } from 'lucide-react';

export default function LoginPage({ isDark }: { isDark: boolean }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login gagal');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className={`min-h-screen flex items-center justify-center ${
        isDark
          ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900'
          : 'bg-gradient-to-br from-blue-50 via-white to-blue-50'
      }`}
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

      <div className="relative z-10 w-full max-w-md px-6">
        <div
          className={`rounded-2xl p-8 ${
            isDark
              ? 'bg-slate-800/40 border border-cyan-500/20'
              : 'bg-white/60 border border-blue-100'
          } backdrop-blur-xl shadow-2xl`}
        >
          <div className="text-center mb-8">
            <h1
              className={`text-3xl font-bold mb-2 ${
                isDark
                  ? 'bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent'
                  : 'text-blue-700'
              }`}
            >
              Selamat Datang
            </h1>
            <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
              Login untuk melanjutkan
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                className={`block text-sm font-medium mb-2 ${
                  isDark ? 'text-cyan-300' : 'text-blue-700'
                }`}
              >
                <Mail className="w-4 h-4 inline mr-2" />
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                required
                className={`w-full px-4 py-3 rounded-lg border ${
                  isDark
                    ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
                    : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
                } backdrop-blur-sm focus:outline-none focus:ring-2 ${
                  isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
                } transition-all duration-300`}
              />
            </div>

            <div>
              <label
                className={`block text-sm font-medium mb-2 ${
                  isDark ? 'text-cyan-300' : 'text-blue-700'
                }`}
              >
                <Lock className="w-4 h-4 inline mr-2" />
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={6}
                className={`w-full px-4 py-3 rounded-lg border ${
                  isDark
                    ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
                    : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
                } backdrop-blur-sm focus:outline-none focus:ring-2 ${
                  isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
                } transition-all duration-300`}
              />
            </div>

            {error && (
              <div
                className={`p-3 rounded-lg ${
                  isDark ? 'bg-red-500/10 border border-red-500/30' : 'bg-red-50 border border-red-200'
                }`}
              >
                <p className={`text-sm ${isDark ? 'text-red-300' : 'text-red-700'}`}>{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all duration-300 ${
                isDark
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500'
                  : 'bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800'
              } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]`}
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader className="w-5 h-5 animate-spin" />
                  Logging in...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <LogIn className="w-5 h-5" />
                  Login
                </span>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
              Tidak bisa mendaftar sendiri. Hubungi Admin Meta untuk membuat akun.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
