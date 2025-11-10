import { useState, useEffect } from 'react';
import { Users, UserCheck, FileText, Calendar, TrendingUp, Plus, Ban, Clock, Trash2 } from 'lucide-react';
import { apiService, User } from '../lib/api';

interface UserStats {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  active_until: string | null;
  total_analyses: number;
  last_analysis: string | null;
}

interface OverallStats {
  total_users: number;
  active_users: number;
  total_analyses: number;
  analyses_today: number;
  analyses_this_week: number;
  analyses_this_month: number;
}

interface AdminMetaDashboardProps {
  isDark: boolean;
}

export default function AdminMetaDashboard({ isDark }: AdminMetaDashboardProps) {
  const [adminRSUsers, setAdminRSUsers] = useState<User[]>([]);
  const [userStats, setUserStats] = useState<UserStats[]>([]);
  const [overallStats, setOverallStats] = useState<OverallStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<'users' | 'statistics'>('users');

  // Create form state
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    active_until: '',
  });

  // Load all Admin RS users
  const loadAdminRSUsers = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getAllAdminRS();
      setAdminRSUsers(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load Admin RS users');
    } finally {
      setIsLoading(false);
    }
  };

  // Load statistics
  const loadStatistics = async () => {
    try {
      const [userStatsResponse, overallStatsResponse] = await Promise.all([
        apiService.getUserStatistics(),
        apiService.getOverallStatistics(),
      ]);
      setUserStats(userStatsResponse.data);
      setOverallStats(overallStatsResponse.data);
    } catch (err: any) {
      console.error('Failed to load statistics:', err);
    }
  };

  useEffect(() => {
    loadAdminRSUsers();
    loadStatistics();
  }, []);

  // Handle create Admin RS
  const handleCreateAdminRS = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const data = {
        ...formData,
        active_until: formData.active_until || null,
      };
      await apiService.createAdminRS(data);
      setShowCreateForm(false);
      setFormData({ email: '', password: '', full_name: '', active_until: '' });
      await loadAdminRSUsers();
      await loadStatistics();
      alert('Admin RS account created successfully');
    } catch (err: any) {
      alert(err.message || 'Failed to create Admin RS account');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle toggle active status
  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await apiService.updateAdminRSStatus(userId, {
        is_active: !currentStatus,
      });
      await loadAdminRSUsers();
    } catch (err: any) {
      alert(err.message || 'Failed to update status');
    }
  };

  // Handle extend expiration
  const handleExtendExpiration = async (userId: number) => {
    const days = prompt('Extend account for how many days?');
    if (!days) return;

    const daysNum = parseInt(days);
    if (isNaN(daysNum) || daysNum <= 0) {
      alert('Please enter a valid number of days');
      return;
    }

    const newDate = new Date();
    newDate.setDate(newDate.getDate() + daysNum);

    try {
      await apiService.updateAdminRSStatus(userId, {
        active_until: newDate.toISOString(),
      });
      await loadAdminRSUsers();
      alert(`Account extended for ${daysNum} days`);
    } catch (err: any) {
      alert(err.message || 'Failed to extend account');
    }
  };

  // Handle delete
  const handleDelete = async (userId: number, email: string) => {
    if (!confirm(`Are you sure you want to delete ${email}?`)) return;

    try {
      await apiService.deleteAdminRS(userId);
      await loadAdminRSUsers();
      alert('Admin RS account deleted successfully');
    } catch (err: any) {
      alert(err.message || 'Failed to delete account');
    }
  };

  // Format date
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'No expiration';
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Check if account is expired
  const isExpired = (dateString: string | null | undefined) => {
    if (!dateString) return false;
    return new Date(dateString) < new Date();
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="mb-8">
          <h2 className={`text-3xl font-semibold mb-6 ${
            isDark ? 'text-cyan-300' : 'text-blue-900'
          }`}>
            Admin Meta Dashboard
          </h2>
          
          {/* Overall Statistics Cards */}
          {overallStats && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              <div className={`p-6 rounded-lg shadow-md border-none ${
                isDark
                  ? 'bg-slate-700/50 border border-slate-600/50'
                  : 'bg-blue-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className={`text-sm mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>Total Users</p>
                    <p className={`text-3xl font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-900'}`}>{overallStats.total_users}</p>
                  </div>
                  <div className={`opacity-60 ${isDark ? 'text-cyan-300' : 'text-blue-900'}`}>
                    <Users className="h-8 w-8" />
                  </div>
                </div>
              </div>
              <div className={`p-6 rounded-lg shadow-md border-none ${
                isDark
                  ? 'bg-slate-700/50 border border-slate-600/50'
                  : 'bg-green-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className={`text-sm mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>Active Users</p>
                    <p className={`text-3xl font-semibold ${isDark ? 'text-green-300' : 'text-green-900'}`}>{overallStats.active_users}</p>
                  </div>
                  <div className={`opacity-60 ${isDark ? 'text-green-300' : 'text-green-900'}`}>
                    <UserCheck className="h-8 w-8" />
                  </div>
                </div>
              </div>
              <div className={`p-6 rounded-lg shadow-md border-none ${
                isDark
                  ? 'bg-slate-700/50 border border-slate-600/50'
                  : 'bg-purple-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className={`text-sm mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>Total Analyses</p>
                    <p className={`text-3xl font-semibold ${isDark ? 'text-blue-300' : 'text-purple-900'}`}>{overallStats.total_analyses.toLocaleString()}</p>
                  </div>
                  <div className={`opacity-60 ${isDark ? 'text-blue-300' : 'text-purple-900'}`}>
                    <FileText className="h-8 w-8" />
                  </div>
                </div>
              </div>
              <div className={`p-6 rounded-lg shadow-md border-none ${
                isDark
                  ? 'bg-slate-700/50 border border-slate-600/50'
                  : 'bg-orange-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className={`text-sm mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>Today</p>
                    <p className={`text-3xl font-semibold ${isDark ? 'text-purple-300' : 'text-orange-900'}`}>{overallStats.analyses_today}</p>
                  </div>
                  <div className={`opacity-60 ${isDark ? 'text-purple-300' : 'text-orange-900'}`}>
                    <Calendar className="h-8 w-8" />
                  </div>
                </div>
              </div>
              <div className={`p-6 rounded-lg shadow-md border-none ${
                isDark
                  ? 'bg-slate-700/50 border border-slate-600/50'
                  : 'bg-pink-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className={`text-sm mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>This Week</p>
                    <p className={`text-3xl font-semibold ${isDark ? 'text-yellow-300' : 'text-pink-900'}`}>{overallStats.analyses_this_week}</p>
                  </div>
                  <div className={`opacity-60 ${isDark ? 'text-yellow-300' : 'text-pink-900'}`}>
                    <TrendingUp className="h-8 w-8" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Create Button Section */}
        <div className="flex justify-between items-center mb-6">
          <div></div>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              isDark
                ? 'bg-cyan-600 text-white hover:bg-cyan-700'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            <Plus className="h-4 w-4" />
            Create Admin RS
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'users'
                ? isDark
                  ? 'bg-cyan-600 text-white'
                  : 'bg-blue-600 text-white'
                : isDark
                  ? 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            User Management
          </button>
          <button
            onClick={() => setActiveTab('statistics')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'statistics'
                ? isDark
                  ? 'bg-cyan-600 text-white'
                  : 'bg-blue-600 text-white'
                : isDark
                  ? 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Usage Statistics
          </button>
        </div>

        {/* Modal Create Form */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowCreateForm(false)}>
            <div 
              className={`${
                isDark
                  ? 'bg-slate-800 border border-slate-700'
                  : 'bg-white border border-gray-200'
              } rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl`}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-4">
                <h2 className={`text-xl font-semibold ${
                  isDark ? 'text-cyan-300' : 'text-blue-700'
                }`}>Create New Admin RS</h2>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className={`text-2xl ${isDark ? 'text-slate-400 hover:text-slate-200' : 'text-gray-400 hover:text-gray-600'}`}
                >
                  ×
                </button>
              </div>
              <p className={`text-sm mb-4 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                Add a new hospital administrator account. Fill in all required fields.
              </p>
              
              <form onSubmit={handleCreateAdminRS} className="space-y-4">
                <div>
                  <label className={`block text-sm font-medium mb-2 ${
                    isDark ? 'text-slate-300' : 'text-gray-700'
                  }`}>
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className={`w-full px-4 py-2 rounded-lg focus:ring-2 focus:border-transparent ${
                      isDark
                        ? 'bg-slate-700 border border-slate-600 text-white focus:ring-cyan-500'
                        : 'bg-white border border-gray-300 text-gray-900 focus:ring-blue-500'
                    }`}
                    placeholder="admin@hospital.id"
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-2 ${
                    isDark ? 'text-slate-300' : 'text-gray-700'
                  }`}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className={`w-full px-4 py-2 rounded-lg focus:ring-2 focus:border-transparent ${
                      isDark
                        ? 'bg-slate-700 border border-slate-600 text-white focus:ring-cyan-500'
                        : 'bg-white border border-gray-300 text-gray-900 focus:ring-blue-500'
                    }`}
                    placeholder="RS Name"
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-2 ${
                    isDark ? 'text-slate-300' : 'text-gray-700'
                  }`}>
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className={`w-full px-4 py-2 rounded-lg focus:ring-2 focus:border-transparent ${
                      isDark
                        ? 'bg-slate-700 border border-slate-600 text-white focus:ring-cyan-500'
                        : 'bg-white border border-gray-300 text-gray-900 focus:ring-blue-500'
                    }`}
                    placeholder="Minimum 6 characters"
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-2 ${
                    isDark ? 'text-slate-300' : 'text-gray-700'
                  }`}>
                    Active Until
                  </label>
                  <input
                    type="date"
                    value={formData.active_until}
                    onChange={(e) => setFormData({ ...formData, active_until: e.target.value })}
                    className={`w-full px-4 py-2 rounded-lg focus:ring-2 focus:border-transparent ${
                      isDark
                        ? 'bg-slate-700 border border-slate-600 text-white focus:ring-cyan-500'
                        : 'bg-white border border-gray-300 text-gray-900 focus:ring-blue-500'
                    }`}
                    placeholder="dd / mm / yyyy"
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                      isDark
                        ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                      isDark
                        ? 'bg-cyan-600 text-white hover:bg-cyan-700 disabled:bg-slate-600'
                        : 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400'
                    }`}
                  >
                    {isSubmitting ? 'Creating...' : 'Create Account'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Admin RS Users List */}
        {activeTab === 'users' && (
          <div className={`shadow-lg rounded-xl border-0 ${
            isDark ? 'bg-slate-800/40 border border-cyan-500/20' : 'bg-white'
          }`}>
            <div className={`p-6 rounded-t-xl border-b ${
              isDark
                ? 'bg-slate-700/50 border-slate-600'
                : 'bg-gradient-to-r from-blue-50 to-blue-100 border-gray-200'
            }`}>
              <h2 className={`text-xl font-semibold ${
                isDark ? 'text-cyan-300' : 'text-blue-900'
              }`}>
                Admin RS Accounts
              </h2>
            </div>
            <div className="p-6">
              {isLoading ? (
                <div className="text-center py-8">
                  <div className={`inline-block animate-spin rounded-full h-8 w-8 border-b-2 ${
                    isDark ? 'border-cyan-500' : 'border-blue-500'
                  }`}></div>
                  <p className={`mt-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>Loading...</p>
                </div>
              ) : error ? (
                <div className={`p-4 rounded-lg ${
                  isDark
                    ? 'bg-red-900/30 border border-red-500/50 text-red-300'
                    : 'bg-red-50 border border-red-300 text-red-700'
                }`}>
                  {error}
                </div>
              ) : adminRSUsers.length === 0 ? (
                <div className={`text-center py-8 ${
                  isDark ? 'text-slate-400' : 'text-gray-600'
                }`}>
                  No Admin RS accounts found. Create one to get started.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className={`min-w-full ${
                    isDark ? 'divide-y divide-slate-700' : 'divide-y divide-gray-200'
                  }`}>
                    <thead>
                      <tr className={`border-b-2 ${
                        isDark ? 'border-slate-600' : 'border-gray-200'
                      }`}>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Email
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Full Name
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Status
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Active Until
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Created At
                        </th>
                        <th className={`px-6 py-3 text-right text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className={`${
                      isDark
                        ? 'bg-slate-800/20 divide-y divide-slate-700'
                        : 'bg-white divide-y divide-gray-100'
                    }`}>
                      {adminRSUsers.map((user) => (
                        <tr key={user.id} className={`transition-colors ${
                          isDark ? 'hover:bg-slate-700/30' : 'hover:bg-blue-50/50'
                        }`}>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                            isDark ? 'text-slate-200' : 'text-gray-700'
                          }`}>
                            {user.email}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                            isDark ? 'text-slate-200' : 'text-gray-900'
                          }`}>
                            {user.full_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.is_active && !isExpired(user.active_until)
                                  ? isDark
                                    ? 'bg-green-900/30 text-green-300 border border-green-500/50'
                                    : 'bg-green-100 text-green-800 border border-green-200'
                                  : isDark
                                    ? 'bg-red-900/30 text-red-300 border border-red-500/50'
                                    : 'bg-gray-100 text-gray-600 border border-gray-200'
                              }`}
                            >
                              {user.is_active && !isExpired(user.active_until) ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                            isDark ? 'text-slate-200' : 'text-gray-700'
                          }`}>
                            <div>
                              {formatDate(user.active_until)}
                              {isExpired(user.active_until) && (
                                <span className={`text-xs block ${
                                  isDark ? 'text-red-400' : 'text-red-600'
                                }`}>Expired</span>
                              )}
                            </div>
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                            isDark ? 'text-slate-200' : 'text-gray-700'
                          }`}>
                            {formatDate(user.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleToggleStatus(user.id, !user.is_active)}
                                className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-all shadow-sm flex items-center gap-1.5 ${
                                  isDark
                                    ? 'bg-slate-800 text-red-400 border-red-500/50 hover:bg-red-600 hover:text-white hover:border-red-600'
                                    : 'bg-white text-red-600 border-red-300 hover:bg-red-600 hover:text-white hover:border-red-600'
                                }`}
                              >
                                <Ban className="h-3.5 w-3.5" />
                                Deactivate
                              </button>
                              <button
                                onClick={() => handleExtendExpiration(user.id)}
                                className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-all shadow-sm flex items-center gap-1.5 ${
                                  isDark
                                    ? 'bg-slate-800 text-teal-400 border-teal-500/50 hover:bg-teal-600 hover:text-white hover:border-teal-600'
                                    : 'bg-white text-teal-600 border-teal-300 hover:bg-teal-600 hover:text-white hover:border-teal-600'
                                }`}
                              >
                                <Clock className="h-3.5 w-3.5" />
                                Extend
                              </button>
                              <button
                                onClick={() => handleDelete(user.id, user.email)}
                                className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-all shadow-sm flex items-center gap-1.5 ${
                                  isDark
                                    ? 'bg-slate-800 text-red-500 border-red-600/50 hover:bg-red-700 hover:text-white hover:border-red-700'
                                    : 'bg-white text-red-700 border-red-400 hover:bg-red-700 hover:text-white hover:border-red-700'
                                }`}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Usage Statistics */}
        {activeTab === 'statistics' && (
          <div className={`shadow-lg rounded-xl border-0 ${
            isDark ? 'bg-slate-800/40 border border-cyan-500/20' : 'bg-white'
          }`}>
            <div className={`p-6 rounded-t-xl border-b ${
              isDark
                ? 'bg-slate-700/50 border-slate-600'
                : 'bg-gradient-to-r from-blue-50 to-blue-100 border-gray-200'
            }`}>
              <h2 className={`text-xl font-semibold ${
                isDark ? 'text-cyan-300' : 'text-blue-900'
              }`}>
                Usage Statistics per Admin RS
              </h2>
            </div>
            <div className="p-6">
              {userStats.length === 0 ? (
                <div className={`text-center py-8 ${
                  isDark ? 'text-slate-400' : 'text-gray-500'
                }`}>
                  No statistics available yet.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className={`min-w-full divide-y ${
                    isDark ? 'divide-slate-700' : 'divide-gray-200'
                  }`}>
                    <thead>
                      <tr className={`border-b-2 ${
                        isDark ? 'border-slate-600' : 'border-gray-200'
                      }`}>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Full Name
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Email
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Status
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Total Analyses
                        </th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDark ? 'text-slate-300' : 'text-gray-700'
                        }`}>
                          Last Analysis
                        </th>
                      </tr>
                    </thead>
                    <tbody className={`${
                      isDark
                        ? 'bg-slate-800/20 divide-y divide-slate-700'
                        : 'bg-white divide-y divide-gray-100'
                    }`}>
                      {userStats.map((stat) => (
                        <tr key={stat.user_id} className={`transition-colors ${
                          isDark ? 'hover:bg-slate-700/30' : 'hover:bg-blue-50/50'
                        }`}>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                            isDark ? 'text-slate-200' : 'text-gray-900'
                          }`}>
                            {stat.full_name}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                            isDark ? 'text-slate-200' : 'text-gray-700'
                          }`}>
                            {stat.email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                stat.is_active && !isExpired(stat.active_until)
                                  ? isDark
                                    ? 'bg-green-900/30 text-green-300 border border-green-500/50'
                                    : 'bg-green-100 text-green-800 border border-green-200'
                                  : isDark
                                    ? 'bg-red-900/30 text-red-300 border border-red-500/50'
                                    : 'bg-gray-100 text-gray-600 border border-gray-200'
                              }`}
                            >
                              {stat.is_active && !isExpired(stat.active_until) ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`${
                              isDark ? 'text-cyan-400' : 'text-blue-600'
                            }`}>
                              {stat.total_analyses}
                            </span>
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                            isDark ? 'text-slate-200' : 'text-gray-700'
                          }`}>
                            {stat.last_analysis ? formatDate(stat.last_analysis) : 'Never'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
