import { FileText } from 'lucide-react';
import { ICD9Detail } from './ICD9CategoryPanel';

interface ICD9DetailPanelProps {
  headCode: string | null;
  details: ICD9Detail[];
  isDark: boolean;
  isLoading?: boolean;
  selectedCode?: string | null;
  onSelectCode?: (code: string, name: string) => void;
}

export default function ICD9DetailPanel({
  headCode,
  details,
  isDark,
  isLoading = false,
  selectedCode = null,
  onSelectCode,
}: ICD9DetailPanelProps) {
  // Show empty state if no head selected
  if (!headCode) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <FileText className="w-12 h-12 mb-3 opacity-30" />
        <p className="text-sm text-center">
          Pilih kategori untuk melihat detail sub-kode ICD-9
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <div className={`w-8 h-8 border-3 ${isDark ? 'border-cyan-500/30 border-t-cyan-500' : 'border-blue-500/30 border-t-blue-500'} rounded-full animate-spin mb-3`} />
        <p className="text-sm">Memuat detail...</p>
      </div>
    );
  }

  if (details.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <FileText className="w-12 h-12 mb-3 opacity-30" />
        <p className="text-sm text-center px-4">
          Tidak ada sub-kode ditemukan untuk {headCode}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-4">
      <div className={`pb-3 border-b ${isDark ? 'border-cyan-500/20' : 'border-blue-200'}`}>
        <h3 className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          Detail Sub-Kode: {headCode}
        </h3>
        <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
          {details.length} sub-kode tersedia
        </p>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {details.map((detail, index) => (
          <button
            key={detail.code}
            onClick={() => onSelectCode?.(detail.code, detail.name)}
            className={`w-full px-4 py-3 rounded-lg transition-all duration-200 text-left ${
              selectedCode === detail.code
                ? isDark
                  ? 'bg-cyan-500/20 border-2 border-cyan-500/50 shadow-lg shadow-cyan-500/20'
                  : 'bg-blue-50 border-2 border-blue-400 shadow-lg shadow-blue-500/10'
                : isDark
                ? 'bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/50 hover:border-cyan-500/30'
                : 'bg-white/50 border border-gray-200 hover:bg-white hover:border-blue-300'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold ${
                selectedCode === detail.code
                  ? isDark ? 'bg-cyan-500/30 text-cyan-300' : 'bg-blue-100 text-blue-700'
                  : isDark ? 'bg-cyan-500/20 text-cyan-300' : 'bg-blue-100 text-blue-700'
              }`}>
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start gap-2 mb-1 flex-wrap">
                  <span
                    className={`text-sm font-bold ${
                      selectedCode === detail.code
                        ? isDark ? 'text-cyan-300' : 'text-blue-700'
                        : isDark ? 'text-cyan-300' : 'text-blue-700'
                    }`}
                  >
                    {detail.code}
                  </span>
                  {selectedCode === detail.code && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        isDark
                          ? 'bg-cyan-500/30 text-cyan-200'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      ✓ Dipilih
                    </span>
                  )}
                </div>
                <p
                  className={`text-sm leading-relaxed font-medium ${
                    selectedCode === detail.code
                      ? isDark ? 'text-slate-200' : 'text-gray-800'
                      : isDark ? 'text-slate-300' : 'text-gray-700'
                  }`}
                >
                  {detail.name}
                </p>
                {/* Common term (Istilah Umum) */}
                {detail.commonTerm && (
                  <div className={`mt-2 px-3 py-1.5 rounded ${
                    selectedCode === detail.code
                      ? isDark ? 'bg-cyan-500/10 border-l-2 border-cyan-400' : 'bg-blue-50 border-l-2 border-blue-500'
                      : isDark ? 'bg-slate-700/30 border-l-2 border-slate-600' : 'bg-gray-50 border-l-2 border-gray-400'
                  }`}>
                    <p className={`text-xs font-medium ${
                      selectedCode === detail.code
                        ? isDark ? 'text-cyan-300' : 'text-blue-700'
                        : isDark ? 'text-slate-400' : 'text-gray-600'
                    }`}>
                      {detail.commonTerm}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className={`pt-3 border-t ${isDark ? 'border-cyan-500/20' : 'border-blue-200'}`}>
        <div className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'} space-y-1`}>
          <p className="italic">
            💡 ICD-9 untuk tindakan medis dan prosedur diagnostik
          </p>
        </div>
      </div>
    </div>
  );
}
