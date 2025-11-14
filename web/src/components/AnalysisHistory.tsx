import React, { useState, useEffect } from 'react';
import api from '../lib/api';

interface AnalysisLog {
  id: number;
  analysis_id: string;
  user_id: number;
  user_email?: string;
  user_name?: string;
  diagnosis: string;
  procedure: string;
  medication: string;
  icd10_code?: string;
  severity?: string;
  total_cost?: number;
  processing_time_ms?: number;
  ai_calls_count?: number;
  status: string;
  created_at: string;
  analysis_result?: any;
  input_data?: any;
}

interface AnalysisHistoryProps {
  userId?: number; // If provided, shows only this user's history
  isAdmin?: boolean; // If true, shows all users' history
}

export const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({ userId, isAdmin = false }) => {
  const [logs, setLogs] = useState<AnalysisLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AnalysisLog | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  
  // Search and filter states
  const [searchText, setSearchText] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 20;

  useEffect(() => {
    fetchLogs();
  }, [userId, searchText, startDate, endDate, currentPage]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      // Use different endpoints for Admin RS vs Admin Meta
      let endpoint = isAdmin ? '/admin/analysis-logs' : '/ai/my-history';
      const params = new URLSearchParams();

      // Admin Meta can filter by user_id, Admin RS automatically filtered
      if (isAdmin && userId) {
        params.append('user_id', userId.toString());
      }
      if (searchText) {
        params.append('search', searchText);
      }
      if (startDate) {
        params.append('start_date', startDate);
      }
      if (endDate) {
        params.append('end_date', endDate);
      }
      params.append('limit', logsPerPage.toString());
      params.append('offset', ((currentPage - 1) * logsPerPage).toString());

      const response = await api.request(`${endpoint}?${params.toString()}`);
      
      if (response.success) {
        setLogs(response.data);
      } else {
        setError(response.message || 'Failed to load analysis history');
      }
    } catch (err: any) {
      console.error('Error fetching analysis logs:', err);
      setError(err.message || 'Failed to load analysis history');
    } finally {
      setLoading(false);
    }
  };

  const viewDetail = async (log: AnalysisLog) => {
    try {
      // Fetch full detail if not already loaded
      if (!log.analysis_result) {
        const endpoint = isAdmin ? `/admin/analysis-logs/${log.id}` : `/ai/my-history/${log.id}`;
        const response = await api.request(endpoint);
        if (response.success) {
          setSelectedLog(response.data);
        } else {
          setSelectedLog(log);
        }
      } else {
        setSelectedLog(log);
      }
      setShowDetail(true);
    } catch (err) {
      console.error('Error fetching log detail:', err);
      setSelectedLog(log);
      setShowDetail(true);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (amount?: number) => {
    if (!amount) return '-';
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
    }).format(amount);
  };

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  const getSeverityBadge = (severity?: string) => {
    if (!severity) return '-';
    
    const severityColors: Record<string, string> = {
      ringan: 'bg-blue-100 text-blue-800',
      sedang: 'bg-yellow-100 text-yellow-800',
      berat: 'bg-red-100 text-red-800',
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${severityColors[severity] || 'bg-gray-100 text-gray-800'}`}>
        {severity}
      </span>
    );
  };

  if (loading && logs.length === 0) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">
          {isAdmin ? 'Riwayat Analisis (Semua User)' : 'Riwayat Analisis Saya'}
        </h2>
        <button
          onClick={fetchLogs}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Search and Filter */}
      <div className="bg-white p-4 rounded-lg shadow space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            type="text"
            placeholder="🔍 Cari diagnosis, tindakan, obat..."
            value={searchText}
            onChange={(e) => {
              setSearchText(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Dari tanggal"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Sampai tanggal"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          ❌ {error}
        </div>
      )}

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tanggal
                </th>
                {isAdmin && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Diagnosis
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ICD-10
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Biaya
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Waktu Proses
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Aksi
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 9 : 8} className="px-6 py-8 text-center text-gray-500">
                    📋 Belum ada riwayat analisis
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(log.created_at)}
                    </td>
                    {isAdmin && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{log.user_name}</div>
                          <div className="text-gray-500 text-xs">{log.user_email}</div>
                        </div>
                      </td>
                    )}
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                      {log.diagnosis}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {log.icd10_code || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {getSeverityBadge(log.severity)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(log.total_cost)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.processing_time_ms ? `${(log.processing_time_ms / 1000).toFixed(1)}s` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {getStatusBadge(log.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => viewDetail(log)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        📄 Detail
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {logs.length > 0 && (
          <div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t border-gray-200">
            <div className="text-sm text-gray-700">
              Halaman {currentPage}
            </div>
            <div className="space-x-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Prev
              </button>
              <button
                onClick={() => setCurrentPage(p => p + 1)}
                disabled={logs.length < logsPerPage}
                className="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetail && selectedLog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-900">
                Detail Analisis - {selectedLog.analysis_id || `#${selectedLog.id}`}
              </h3>
              <button
                onClick={() => setShowDetail(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
              >
                ×
              </button>
            </div>

            <div className="px-6 py-4 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tanggal</label>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(selectedLog.created_at)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <p className="mt-1">{getStatusBadge(selectedLog.status)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">ICD-10</label>
                  <p className="mt-1 text-sm font-mono text-gray-900">{selectedLog.icd10_code || '-'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Severity</label>
                  <p className="mt-1">{getSeverityBadge(selectedLog.severity)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Waktu Proses</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedLog.processing_time_ms ? `${(selectedLog.processing_time_ms / 1000).toFixed(2)}s` : '-'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">AI Calls</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedLog.ai_calls_count || '-'} calls</p>
                </div>
              </div>

              {/* Input Data */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3">📝 Input Data</h4>
                <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                  <div>
                    <span className="font-medium text-gray-700">Diagnosis:</span>
                    <p className="text-gray-900">{selectedLog.diagnosis}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Tindakan:</span>
                    <p className="text-gray-900">{selectedLog.procedure || '-'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Obat:</span>
                    <p className="text-gray-900">{selectedLog.medication || '-'}</p>
                  </div>
                </div>
              </div>

              {/* Analysis Result */}
              {selectedLog.analysis_result && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">📊 Hasil Analisis</h4>
                  <div className="bg-blue-50 p-4 rounded-lg space-y-4">
                    
                    {/* Diagnosis Info */}
                    {selectedLog.analysis_result.diagnosis && (
                      <div>
                        <h5 className="font-semibold text-gray-800 mb-2">Diagnosis</h5>
                        <div className="bg-white p-3 rounded">
                          <p className="text-sm"><span className="font-medium">ICD-10:</span> {selectedLog.analysis_result.diagnosis.icd10?.kode_icd} - {selectedLog.analysis_result.diagnosis.icd10?.nama}</p>
                          <p className="text-sm"><span className="font-medium">Severity:</span> {selectedLog.analysis_result.diagnosis.severity}</p>
                          <p className="text-sm"><span className="font-medium">Justifikasi:</span> {selectedLog.analysis_result.diagnosis.justifikasi_klinis}</p>
                        </div>
                      </div>
                    )}

                    {/* Fornas Results */}
                    {selectedLog.analysis_result.obat_results && (
                      <div>
                        <h5 className="font-semibold text-gray-800 mb-2">Validasi Obat Fornas</h5>
                        <div className="bg-white p-3 rounded space-y-2">
                          {selectedLog.analysis_result.obat_results.map((obat: any, idx: number) => (
                            <div key={idx} className="border-b border-gray-200 pb-2 last:border-b-0">
                              <p className="text-sm font-medium">{obat.obat_input}</p>
                              <p className="text-sm text-gray-600">Match: {obat.fornas_match?.nama_obat || 'Tidak ditemukan'}</p>
                              <p className="text-sm">
                                <span className={obat.is_sesuai ? 'text-green-600' : 'text-red-600'}>
                                  {obat.is_sesuai ? '✓ Sesuai' : '✗ Tidak Sesuai'}
                                </span>
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Clinical Pathway */}
                    {selectedLog.analysis_result.clinical_pathway && (
                      <div>
                        <h5 className="font-semibold text-gray-800 mb-2">Clinical Pathway</h5>
                        <div className="bg-white p-3 rounded">
                          <pre className="text-xs whitespace-pre-wrap text-gray-700">
                            {selectedLog.analysis_result.clinical_pathway}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Cost Estimate */}
                    {selectedLog.total_cost && (
                      <div>
                        <h5 className="font-semibold text-gray-800 mb-2">Estimasi Biaya</h5>
                        <div className="bg-white p-3 rounded">
                          <p className="text-lg font-bold text-green-600">{formatCurrency(selectedLog.total_cost)}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Raw JSON (for debugging) */}
              <details className="border border-gray-300 rounded-lg">
                <summary className="px-4 py-2 bg-gray-100 cursor-pointer hover:bg-gray-200 rounded-t-lg font-medium">
                  🔧 Raw Data (JSON)
                </summary>
                <pre className="p-4 text-xs overflow-auto max-h-96 bg-gray-50">
                  {JSON.stringify(selectedLog.analysis_result || selectedLog, null, 2)}
                </pre>
              </details>
            </div>

            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4">
              <button
                onClick={() => setShowDetail(false)}
                className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisHistory;
