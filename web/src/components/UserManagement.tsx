import { useState, useEffect } from 'react';
import { Users, Edit2, Save, X } from 'lucide-react';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  active_until: string | null;
  daily_ai_limit: number;
  ai_usage_count: number;
  ai_usage_date: string;
  created_at: string;
}

interface UserManagementProps {
  isDark: boolean;
}

export default function UserManagement({ isDark }: UserManagementProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editLimit, setEditLimit] = useState<number>(100);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/admin/admin-rs', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        setUsers(result.data || []);
      } else {
        console.error('Failed to load users');
      }
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditLimit = (user: User) => {
    setEditingUserId(user.id);
    setEditLimit(user.daily_ai_limit);
  };

  const handleSaveLimit = async (userId: number) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/admin/users/${userId}/ai-limit`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ daily_ai_limit: editLimit }),
      });

      if (response.ok) {
        setEditingUserId(null);
        loadUsers(); // Refresh list
      } else {
        const error = await response.json();
        alert(`Failed to update limit: ${error.message}`);
      }
    } catch (error) {
      console.error('Error updating limit:', error);
      alert('Failed to update limit');
    }
  };

  const handleCancelEdit = () => {
    setEditingUserId(null);
    setEditLimit(100);
  };

  const getUsagePercentage = (used: number, limit: number) => {
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageColor = (used: number, limit: number) => {
    const percentage = getUsagePercentage(used, limit);
    if (percentage >= 90) return 'text-red-500';
    if (percentage >= 70) return 'text-yellow-500';
    return 'text-green-500';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className={`h-full rounded-2xl p-6 ${
      isDark ? 'bg-slate-800/40 border border-cyan-500/20' : 'bg-white/60 border border-blue-100'
    } backdrop-blur-xl shadow-2xl overflow-hidden flex flex-col`}>
      <div className="flex items-center gap-3 mb-6">
        <Users className={`w-6 h-6 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
        <h2 className={`text-2xl font-bold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          User Management
        </h2>
      </div>

      <div className="overflow-auto flex-1">
        <table className="w-full">
          <thead>
            <tr className={`border-b-2 ${
              isDark ? 'border-cyan-500/30' : 'border-blue-200'
            }`}>
              <th className={`text-left p-3 font-semibold ${
                isDark ? 'text-cyan-300' : 'text-blue-700'
              }`}>User</th>
              <th className={`text-left p-3 font-semibold ${
                isDark ? 'text-cyan-300' : 'text-blue-700'
              }`}>Status</th>
              <th className={`text-center p-3 font-semibold ${
                isDark ? 'text-cyan-300' : 'text-blue-700'
              }`}>Daily Limit</th>
              <th className={`text-center p-3 font-semibold ${
                isDark ? 'text-cyan-300' : 'text-blue-700'
              }`}>Today Usage</th>
              <th className={`text-center p-3 font-semibold ${
                isDark ? 'text-cyan-300' : 'text-blue-700'
              }`}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr 
                key={user.id}
                className={`border-b ${
                  isDark ? 'border-slate-700 hover:bg-slate-700/30' : 'border-gray-200 hover:bg-blue-50/50'
                } transition-colors`}
              >
                <td className="p-3">
                  <div>
                    <div className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                      {user.full_name}
                    </div>
                    <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
                      {user.email}
                    </div>
                  </div>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    user.is_active
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="p-3 text-center">
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
                      {user.daily_ai_limit}
                    </span>
                  )}
                </td>
                <td className="p-3">
                  <div className="flex flex-col items-center gap-1">
                    <span className={`font-bold ${getUsageColor(user.ai_usage_count, user.daily_ai_limit)}`}>
                      {user.ai_usage_count} / {user.daily_ai_limit}
                    </span>
                    <div className={`w-full h-1.5 rounded-full ${isDark ? 'bg-slate-600' : 'bg-gray-200'}`}>
                      <div
                        className={`h-full rounded-full ${
                          getUsagePercentage(user.ai_usage_count, user.daily_ai_limit) >= 90
                            ? 'bg-red-500'
                            : getUsagePercentage(user.ai_usage_count, user.daily_ai_limit) >= 70
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{ width: `${getUsagePercentage(user.ai_usage_count, user.daily_ai_limit)}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="p-3">
                  <div className="flex items-center justify-center gap-2">
                    {editingUserId === user.id ? (
                      <>
                        <button
                          onClick={() => handleSaveLimit(user.id)}
                          className={`p-1.5 rounded hover:bg-green-500/20 ${
                            isDark ? 'text-green-400' : 'text-green-600'
                          }`}
                          title="Save"
                        >
                          <Save className="w-4 h-4" />
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className={`p-1.5 rounded hover:bg-red-500/20 ${
                            isDark ? 'text-red-400' : 'text-red-600'
                          }`}
                          title="Cancel"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleEditLimit(user)}
                        className={`p-1.5 rounded hover:bg-cyan-500/20 ${
                          isDark ? 'text-cyan-400' : 'text-blue-600'
                        }`}
                        title="Edit Limit"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {users.length === 0 && (
          <div className={`text-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
            No users found
          </div>
        )}
      </div>
    </div>
  );
}
