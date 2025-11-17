import { useState, useEffect } from 'react';
import { Users, UserCheck, FileText, Calendar, TrendingUp, Plus, Ban, Clock, Trash2, Edit2, Save, X } from 'lucide-react';
import { apiService, User } from '../lib/api';

interface UserStats {
  user_id: number;
  email: string;
  full_name: string;
  tipe_rs: string;
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
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editLimit, setEditLimit] = useState<number>(100);

  // Create form state
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    tipe_rs: '',
    active_until: '',
    daily_ai_limit: 100,
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
      setFormData({ email: '', password: '', full_name: '',tipe_rs: '', active_until: '', daily_ai_limit: 100 });
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
    const days = prompt('Extend account for how many days?', '30');
    if (!days) return;

    const daysNum = parseInt(days);
    if (isNaN(daysNum) || daysNum <= 0) {
      alert('Please enter a valid number of days');
      return;
    }

    // Get current user to check their active_until
    const currentUser = adminRSUsers.find(u => u.id === userId);
    if (!currentUser) return;

    let newDate: Date;
    
    // If account is expired or has no expiration date, extend from today
    if (!currentUser.active_until || new Date(currentUser.active_until) < new Date()) {
      newDate = new Date();
      newDate.setDate(newDate.getDate() + daysNum);
    } else {
      // If account is still active, extend from current expiration date
      newDate = new Date(currentUser.active_until);
      newDate.setDate(newDate.getDate() + daysNum);
    }

    try {
      // Update both active_until and set is_active to true
      await apiService.updateAdminRSStatus(userId, {
        active_until: newDate.toISOString(),
        is_active: true,
      });
      await loadAdminRSUsers();
      alert(`Account extended for ${daysNum} days until ${newDate.toLocaleDateString('id-ID')}`);
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
      await loadStatistics();
      alert('Admin RS account deleted successfully');
    } catch (err: any) {
      alert(err.message || 'Failed to delete account');
    }
  };

  // Handle edit AI limit
  const handleEditLimit = (userId: number, currentLimit: number) => {
    setEditingUserId(userId);
    setEditLimit(currentLimit);
  };

  // Handle save AI limit
  const handleSaveLimit = async (userId: number) => {
    try {
      const response = await apiService.request(`/api/admin/users/${userId}/ai-limit`, {
        method: 'PATCH',
        body: JSON.stringify({ daily_ai_limit: editLimit }),
      });

      if (response.success) {
        setEditingUserId(null);
        await loadAdminRSUsers();
        await loadStatistics();
        alert('AI limit updated successfully');
      }
    } catch (error: any) {
      console.error('Error updating limit:', error);
      alert(`Failed to update limit: ${error.message || 'Unknown error'}`);
    }
  };

  // Handle cancel edit
  const handleCancelEdit = () => {
    setEditingUserId(null);
    setEditLimit(100);
  };

  // Get usage percentage and color
  const getUsagePercentage = (used: number, limit: number) => {
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageColor = (used: number, limit: number) => {
    const percentage = getUsagePercentage(used, limit);
    if (percentage >= 90) return 'text-red-500';
    if (percentage >= 70) return 'text-yellow-500';
    return 'text-green-500';
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

  const formatDateTime = (dateString: string | null | undefined) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
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
          <h3 className={`text-xl font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-900'}`}>
            Comprehensive User Management
          </h3>
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
                    Tipe RS
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.tipe_rs}
                    onChange={(e) => setFormData({ ...formData, tipe_rs: e.target.value })}
                    className={`w-full px-4 py-2 rounded-lg focus:ring-2 focus:border-transparent ${
                      isDark
                        ? 'bg-slate-700 border border-slate-600 text-white focus:ring-cyan-500'
                        : 'bg-white border border-gray-300 text-gray-900 focus:ring-blue-500'
                    }`}
                    placeholder="Contoh: RSUD, RS A, RS B, Klinik"
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

                <div>
                  <label className={`block text-sm font-medium mb-2 ${
                    isDark ? 'text-slate-300' : 'text-gray-700'
                  }`}>
                    Daily AI Limit
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    value={formData.daily_ai_limit}
                    onChange={(e) => setFormData({ ...formData, daily_ai_limit: parseInt(e.target.value) || 100 })}
                    className={`w-full px-4 py-2 rounded-lg focus:ring-2 focus:border-transparent ${
                      isDark
                        ? 'bg-slate-700 border border-slate-600 text-white focus:ring-cyan-500'
                        : 'bg-white border border-gray-300 text-gray-900 focus:ring-blue-500'
                    }`}
                    placeholder="100"
                  />
                  <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
                    Maximum AI analysis requests per day (default: 100)
                  </p>
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

        {/* Comprehensive Admin RS Management Table */}
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
              Admin RS Accounts - Complete Overview
            </h2>
            <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
              Manage users, AI limits, and view usage statistics all in one place
            </p>
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
                      <th className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        isDark ? 'text-slate-300' : 'text-gray-700'
                      }`}>
                        User Info
                      </th>
                      <th className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        isDark ? 'text-slate-300' : 'text-gray-700'
                      }`}>
                        Tipe RS
                      </th>
                      <th className={`px-4 py-3 text-center text-xs font-medium uppercase tracking-wider ${
                        isDark ? 'text-slate-300' : 'text-gray-700'
                      }`}>
                        Status
                      </th>
                      <th className={`px-4 py-3 text-center text-xs font-medium uppercase tracking-wider ${
                        isDark ? 'text-slate-300' : 'text-gray-700'
                      }`}>
                        Daily Limit
                      </th>
                      <th className={`px-4 py-3 text-center text-xs font-medium uppercase tracking-wider ${
                        isDark ? 'text-slate-300' : 'text-gray-700'
                      }`}>
                        Today Usage
                      </th>
                      <th className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        isDark ? 'text-slate-300' : 'text-gray-700'
                      }`}>
                        Total Analyses
                      </th>
                      <th className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        isDark ? 'text-slate-300' : 'text-gray-700'
                      }`}>
                        Active Until
                      </th>
                      <th className={`px-4 py-3 text-center text-xs font-medium uppercase tracking-wider ${
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
                    {adminRSUsers.map((user) => {
                      const userStat = userStats.find(s => s.user_id === user.id);
                      return (
                        <tr key={user.id} className={`transition-colors ${
                          isDark ? 'hover:bg-slate-700/30' : 'hover:bg-blue-50/50'
                        }`}>
                          {/* User Info */}
                          <td className="px-4 py-4">
                            <div>
                              <div className={`font-medium text-sm ${
                                isDark ? 'text-white' : 'text-gray-900'
                              }`}>
                                {user.full_name}
                              </div>
                              <div className={`text-xs ${
                                isDark ? 'text-slate-400' : 'text-gray-500'
                              }`}>
                                {user.email}
                              </div>
                            </div>
                          </td>

                          {/* Tipe RS */}
                          <td className="px-4 py-4 text-center">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              isDark ? 'bg-cyan-900/30 text-cyan-300 border border-cyan-500/50' : 'bg-cyan-100 text-cyan-800 border border-cyan-200'
                            }`}>
                              {user.tipe_rs}
                            </span>
                          </td>
                          
                          {/* Status */}
                          <td className="px-4 py-4 text-center">
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

                          {/* Daily AI Limit - with inline edit */}
                          <td className="px-4 py-4 text-center">
                            {editingUserId === user.id ? (
                              <input
                                type="number"
                                value={editLimit}
                                onChange={(e) => setEditLimit(parseInt(e.target.value) || 0)}
                                className={`w-20 px-2 py-1 rounded border text-center ${
                                  isDark
                                    ? 'bg-slate-700 border-cyan-500/30 text-white'
                                    : 'bg-white border-blue-300 text-gray-900'
                                }`}
                                min="0"
                              />
                            ) : (
                              <span className={`font-bold ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
                                {(user as any).daily_ai_limit || 100}
                              </span>
                            )}
                          </td>

                          {/* Today Usage */}
                          <td className="px-4 py-4">
                            <div className="flex flex-col items-center gap-1">
                              <span className={`font-bold text-sm ${getUsageColor((user as any).ai_usage_count || 0, (user as any).daily_ai_limit || 100)}`}>
                                {(user as any).ai_usage_count || 0} / {(user as any).daily_ai_limit || 100}
                              </span>
                              <div className={`w-full h-1.5 rounded-full ${isDark ? 'bg-slate-600' : 'bg-gray-200'}`}>
                                <div
                                  className={`h-full rounded-full transition-all ${
                                    getUsagePercentage((user as any).ai_usage_count || 0, (user as any).daily_ai_limit || 100) >= 90
                                      ? 'bg-red-500'
                                      : getUsagePercentage((user as any).ai_usage_count || 0, (user as any).daily_ai_limit || 100) >= 70
                                      ? 'bg-yellow-500'
                                      : 'bg-green-500'
                                  }`}
                                  style={{ width: `${getUsagePercentage((user as any).ai_usage_count || 0, (user as any).daily_ai_limit || 100)}%` }}
                                />
                              </div>
                            </div>
                          </td>

                          {/* Total Analyses */}
                          <td className="px-4 py-4">
                            <div>
                              <div className={`font-bold text-sm ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
                                {userStat?.total_analyses || 0} analyses
                              </div>
                              <div className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
                                Last: {formatDateTime(userStat?.last_analysis)}
                              </div>
                            </div>
                          </td>

                          {/* Active Until */}
                          <td className={`px-4 py-4 text-sm ${
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

                          {/* Actions */}
                          <td className="px-4 py-4">
                            <div className="flex flex-col gap-1">
                              {/* AI Limit Edit Buttons */}
                              {editingUserId === user.id ? (
                                <div className="flex items-center justify-center gap-1">
                                  <button
                                    onClick={() => handleSaveLimit(user.id)}
                                    className={`p-1 rounded hover:bg-green-500/20 ${
                                      isDark ? 'text-green-400' : 'text-green-600'
                                    }`}
                                    title="Save Limit"
                                  >
                                    <Save className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={handleCancelEdit}
                                    className={`p-1 rounded hover:bg-red-500/20 ${
                                      isDark ? 'text-red-400' : 'text-red-600'
                                    }`}
                                    title="Cancel"
                                  >
                                    <X className="w-4 h-4" />
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => handleEditLimit(user.id, (user as any).daily_ai_limit || 100)}
                                  className={`px-2 py-1 text-xs font-medium rounded border transition-all shadow-sm flex items-center justify-center gap-1 ${
                                    isDark
                                      ? 'bg-slate-800 text-cyan-400 border-cyan-500/50 hover:bg-cyan-600 hover:text-white'
                                      : 'bg-white text-blue-600 border-blue-300 hover:bg-blue-600 hover:text-white'
                                  }`}
                                >
                                  <Edit2 className="h-3 w-3" />
                                  Edit Limit
                                </button>
                              )}
                              
                              {/* Account Management Buttons */}
                              <div className="flex items-center justify-center gap-1">
                                <button
                                  onClick={() => handleToggleStatus(user.id, user.is_active)}
                                  className={`px-2 py-1 text-xs font-medium rounded border transition-all shadow-sm flex items-center gap-1 ${
                                    isDark
                                      ? 'bg-slate-800 text-red-400 border-red-500/50 hover:bg-red-600 hover:text-white'
                                      : 'bg-white text-red-600 border-red-300 hover:bg-red-600 hover:text-white'
                                  }`}
                                  title={user.is_active ? 'Deactivate' : 'Activate'}
                                >
                                  <Ban className="h-3 w-3" />
                                </button>
                                <button
                                  onClick={() => handleExtendExpiration(user.id)}
                                  className={`px-2 py-1 text-xs font-medium rounded border transition-all shadow-sm flex items-center gap-1 ${
                                    isDark
                                      ? 'bg-slate-800 text-teal-400 border-teal-500/50 hover:bg-teal-600 hover:text-white'
                                      : 'bg-white text-teal-600 border-teal-300 hover:bg-teal-600 hover:text-white'
                                  }`}
                                  title="Extend Expiration"
                                >
                                  <Clock className="h-3 w-3" />
                                </button>
                                <button
                                  onClick={() => handleDelete(user.id, user.email)}
                                  className={`px-2 py-1 text-xs font-medium rounded border transition-all shadow-sm flex items-center gap-1 ${
                                    isDark
                                      ? 'bg-slate-800 text-red-500 border-red-600/50 hover:bg-red-700 hover:text-white'
                                      : 'bg-white text-red-700 border-red-400 hover:bg-red-700 hover:text-white'
                                  }`}
                                  title="Delete Account"
                                >
                                  <Trash2 className="h-3 w-3" />
                                </button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
