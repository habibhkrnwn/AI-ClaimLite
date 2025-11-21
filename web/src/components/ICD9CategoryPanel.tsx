import { ChevronRight, Hash } from 'lucide-react';

export interface ICD9Category {
  headCode: string;
  headName: string;
  commonTerm?: string | null;
  count: number;
  details?: ICD9Detail[];
}

export interface ICD9Detail {
  code: string;
  name: string;
  commonTerm?: string | null;
  explanation?: string | null;
}

interface ICD9CategoryPanelProps {
  categories: ICD9Category[];
  selectedHeadCode: string | null;
  onSelectCategory: (headCode: string) => void;
  isDark: boolean;
  isLoading?: boolean;
}

export default function ICD9CategoryPanel({
  categories,
  selectedHeadCode,
  onSelectCategory,
  isDark,
  isLoading = false,
}: ICD9CategoryPanelProps) {
  if (isLoading) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <div className={`w-8 h-8 border-3 ${isDark ? 'border-cyan-500/30 border-t-cyan-500' : 'border-blue-500/30 border-t-blue-500'} rounded-full animate-spin mb-3`} />
        <p className="text-sm animate-pulse">Memuat kategori...</p>
      </div>
    );
  }

  if (categories.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <div className="relative">
          <Hash className="w-12 h-12 mb-3 opacity-30 animate-bounce" />
          <div className={`absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center ${
            isDark ? 'bg-orange-500/20 text-orange-400' : 'bg-orange-100 text-orange-600'
          }`}>
            <span className="text-xs">!</span>
          </div>
        </div>
        <p className="text-sm text-center px-4 font-medium">
          Tidak ada ICD-9 ditemukan
        </p>
        <p className="text-xs text-center px-4 mt-1 opacity-70">
          Coba kata kunci yang berbeda
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className={`flex-shrink-0 pb-3 mb-3 border-b ${isDark ? 'border-cyan-500/20' : 'border-blue-200'}`}>
        <h3 className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          ICD Utama (Tindakan)
        </h3>
        <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
          {categories.length} kode ditemukan
        </p>
      </div>

      {/* Scrollable category list with fixed height - Max 5 items visible */}
      <div className={`space-y-1 pr-2 overflow-y-auto ${
        isDark 
          ? 'scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-slate-800/20' 
          : 'scrollbar-thin scrollbar-thumb-blue-400/40 scrollbar-track-gray-200/40'
      } hover:scrollbar-thumb-cyan-500/50`}
      style={{ height: '280px', maxHeight: '280px' }}>
        {categories.map((category) => (
          <button
            key={category.headCode}
            onClick={() => onSelectCategory(category.headCode)}
            className={`w-full text-left rounded-md transition-all duration-200 group ${
              selectedHeadCode === category.headCode
                ? isDark
                  ? 'bg-cyan-500/20 border border-cyan-500/50 shadow-md'
                  : 'bg-blue-50 border border-blue-400 shadow-md'
                : isDark
                ? 'bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/50 hover:border-cyan-500/30'
                : 'bg-white/50 border border-gray-200 hover:bg-white hover:border-blue-300'
            }`}
            style={{ height: '55px' }}
          >
            <div className="h-full px-2.5 py-2 flex items-center gap-2.5 overflow-hidden">
              <div className="flex items-center gap-2 flex-shrink-0">
                <span
                  className={`text-base font-bold ${
                    selectedHeadCode === category.headCode
                      ? isDark ? 'text-cyan-300' : 'text-blue-700'
                      : isDark ? 'text-cyan-400' : 'text-blue-600'
                  }`}
                >
                  {category.headCode}
                </span>
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${
                    selectedHeadCode === category.headCode
                      ? isDark ? 'bg-cyan-500/30 text-cyan-200' : 'bg-blue-100 text-blue-700'
                      : isDark ? 'bg-slate-700/50 text-slate-400' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {category.count}
                </span>
              </div>
              <p
                className={`text-sm font-medium flex-1 min-w-0 truncate ${
                  selectedHeadCode === category.headCode
                    ? isDark ? 'text-slate-200' : 'text-gray-800'
                    : isDark ? 'text-slate-300' : 'text-gray-700'
                }`}
                title={category.headName}
              >
                {category.headName}
              </p>
              <ChevronRight
                className={`flex-shrink-0 w-4 h-4 transition-transform duration-200 ${
                  selectedHeadCode === category.headCode
                    ? isDark ? 'text-cyan-400 rotate-90' : 'text-blue-600 rotate-90'
                    : isDark ? 'text-slate-500' : 'text-gray-400'
                }`}
              />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
