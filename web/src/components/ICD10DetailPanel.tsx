import { FileText } from 'lucide-react';
import { ICD10Detail } from './ICD10CategoryPanel';

interface ICD10DetailPanelProps {
  headCode: string | null;
  details: ICD10Detail[];
  isDark: boolean;
  isLoading?: boolean;
  selectedCode?: string | null;
  onSelectCode?: (code: string, name: string) => void;
}

export default function ICD10DetailPanel({
  headCode,
  details,
  isDark,
  isLoading = false,
  selectedCode = null,
  onSelectCode,
}: ICD10DetailPanelProps) {
  // Show empty state if no head selected
  if (!headCode) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <FileText className="w-12 h-12 mb-3 opacity-30" />
        <p className="text-sm text-center">
          Pilih kategori untuk melihat detail sub-kode ICD-10
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
    <div className="flex flex-col">
      <div className={`flex-shrink-0 pb-3 mb-3 border-b ${isDark ? 'border-cyan-500/20' : 'border-blue-200'}`}>
        <h3 className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          Detail Sub-Kode: {headCode}
        </h3>
        <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
          {details.length} sub-kode tersedia
        </p>
      </div>

      {/* Details list - scroll if more than 6 items */}
      <div className={`space-y-2 pr-2 ${
        details.length > 6 ? 'max-h-[400px] overflow-y-auto' : ''
      } ${
        isDark 
          ? 'scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-slate-800/20' 
          : 'scrollbar-thin scrollbar-thumb-blue-400/40 scrollbar-track-gray-200/40'
      } hover:scrollbar-thumb-cyan-500/50`}>
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
                <div className="flex items-center gap-3 mb-1">
                  <span
                    className={`text-lg font-bold flex-shrink-0 ${
                      selectedCode === detail.code
                        ? isDark ? 'text-cyan-300' : 'text-blue-700'
                        : isDark ? 'text-cyan-300' : 'text-blue-700'
                    }`}
                  >
                    {detail.code}
                  </span>
                  <p
                    className={`text-sm font-medium flex-1 min-w-0 ${
                      selectedCode === detail.code
                        ? isDark ? 'text-slate-200' : 'text-gray-800'
                        : isDark ? 'text-slate-300' : 'text-gray-700'
                    }`}
                  >
                    {detail.name}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  {selectedCode === detail.code && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${
                        isDark
                          ? 'bg-cyan-500/30 text-cyan-200'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      ✓ Dipilih
                    </span>
                  )}
                  {detail.code.endsWith('.9') && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${
                        isDark
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      Unspecified
                    </span>
                  )}
                  {detail.code.endsWith('.0') && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${
                        isDark
                          ? 'bg-green-500/20 text-green-300'
                          : 'bg-green-100 text-green-700'
                      }`}
                    >
                      Primary
                    </span>
                  )}
                </div>
                {/* Penjelasan spesifik dari AI */}
                {detail.explanation && (
                  <div className={`mt-2 px-3 py-2 rounded ${
                    selectedCode === detail.code
                      ? isDark ? 'bg-blue-500/10 border-l-2 border-blue-400' : 'bg-blue-50 border-l-2 border-blue-500'
                      : isDark ? 'bg-slate-700/20 border-l-2 border-slate-600' : 'bg-gray-50 border-l-2 border-gray-300'
                  }`}>
                    <p className={`text-xs italic ${
                      selectedCode === detail.code
                        ? isDark ? 'text-blue-300' : 'text-blue-700'
                        : isDark ? 'text-slate-400' : 'text-gray-600'
                    }`}>
                      💡 {detail.explanation}
                    </p>
                  </div>
                )}
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
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isDark ? 'bg-green-500/20' : 'bg-green-100'}`} />
            <span>Kode .0 = Primary/Specific type</span>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isDark ? 'bg-amber-500/20' : 'bg-amber-100'}`} />
            <span>Kode .9 = Unspecified (gunakan jika detail tidak diketahui)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
