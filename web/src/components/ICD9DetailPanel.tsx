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
  const getFriendlyDescription = (detail: ICD9Detail): string => {
    const explanation = detail.explanation?.trim();
    if (explanation) {
      return explanation;
    }

    const commonTerm = detail.commonTerm?.trim();
    if (commonTerm) {
      return commonTerm.charAt(0).toUpperCase() + commonTerm.slice(1);
    }

    const name = detail.name || '';
    const key = name.toLowerCase();

    if (key.includes('adenoviral pneumonia')) {
      return 'Infeksi paru-paru yang disebabkan oleh virus adenovirus.';
    }

    return name;
  };

  // Show empty state if no head selected
  if (!headCode) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <FileText className="w-12 h-12 mb-3 opacity-30" />
        <p className="text-sm text-center">
          Pilih ICD utama untuk melihat ICD turunan
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
          Tidak ada ICD turunan untuk {headCode}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className={`flex-shrink-0 pb-3 mb-3 border-b ${isDark ? 'border-cyan-500/20' : 'border-blue-200'}`}>
        <h3 className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          ICD Turunan: {headCode}
        </h3>
        <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
          {details.length} kode tersedia
        </p>
      </div>

      {/* Details list with fixed height and scroll - Max 5 items visible */}
      <div className={`space-y-1.5 pr-2 overflow-y-auto ${
        isDark 
          ? 'scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-slate-800/20' 
          : 'scrollbar-thin scrollbar-thumb-blue-400/40 scrollbar-track-gray-200/40'
      } hover:scrollbar-thumb-cyan-500/50`}
      style={{ height: '280px', maxHeight: '280px' }}>
        {details.map((detail, index) => (
          <button
            key={detail.code}
            onClick={() => onSelectCode?.(detail.code, detail.name)}
            className={`w-full rounded-md transition-all duration-200 text-left ${
              selectedCode === detail.code
                ? isDark
                  ? 'bg-cyan-500/20 border-2 border-cyan-500/50 shadow-lg shadow-cyan-500/20'
                  : 'bg-blue-50 border-2 border-blue-400 shadow-lg shadow-blue-500/10'
                : isDark
                ? 'bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/50 hover:border-cyan-500/30'
                : 'bg-white/50 border border-gray-200 hover:bg-white hover:border-blue-300'
            }`}
            style={{ minHeight: '55px', maxHeight: '80px' }}
          >
            <div className="h-full px-2.5 py-2 flex items-center gap-2 overflow-hidden">
              <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-semibold ${
                selectedCode === detail.code
                  ? isDark ? 'bg-cyan-500/30 text-cyan-300' : 'bg-blue-100 text-blue-700'
                  : isDark ? 'bg-cyan-500/20 text-cyan-300' : 'bg-blue-100 text-blue-700'
              }`}>
                {index + 1}
              </div>
              <div className="flex-1 min-w-0 overflow-y-auto max-h-full">
                <div className="flex items-center gap-2 flex-wrap flex-shrink-0">
                  <span
                    className={`text-base font-bold flex-shrink-0 ${
                      selectedCode === detail.code
                        ? isDark ? 'text-cyan-300' : 'text-blue-700'
                        : isDark ? 'text-cyan-300' : 'text-blue-700'
                    }`}
                  >
                    {detail.code}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium line-clamp-1 ${
                        selectedCode === detail.code
                          ? isDark ? 'text-slate-200' : 'text-gray-800'
                          : isDark ? 'text-slate-300' : 'text-gray-700'
                      }`}
                      title={detail.name}
                    >
                      {detail.name}
                    </p>
                    <p
                      className={`text-xs mt-0.5 line-clamp-2 ${
                        isDark ? 'text-slate-400' : 'text-gray-500'
                      }`}
                    >
                      {getFriendlyDescription(detail)}
                    </p>
                  </div>
                  {selectedCode === detail.code && (
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded-full flex-shrink-0 ${
                        isDark
                          ? 'bg-cyan-500/30 text-cyan-200'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      ✓ Dipilih
                    </span>
                  )}
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
