import { ChevronRight, Hash } from 'lucide-react';

export interface ICD10Category {
  headCode: string;
  headName: string;
  commonTerm?: string | null;
  count: number;
  details?: ICD10Detail[];
}

export interface ICD10Detail {
  code: string;
  name: string;
  commonTerm?: string | null;
  explanation?: string | null;
}

// Alias untuk ICD-9 (struktur sama)
export type ICD9Category = ICD10Category;
export type ICD9Detail = ICD10Detail;

interface ICD10CategoryPanelProps {
  categories: ICD10Category[];
  selectedHeadCode: string | null;
  onSelectCategory: (headCode: string) => void;
  isDark: boolean;
  isLoading?: boolean;
}

export default function ICD10CategoryPanel({
  categories,
  selectedHeadCode,
  onSelectCategory,
  isDark,
  isLoading = false,
}: ICD10CategoryPanelProps) {
  if (isLoading) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <div className={`w-8 h-8 border-3 ${isDark ? 'border-cyan-500/30 border-t-cyan-500' : 'border-blue-500/30 border-t-blue-500'} rounded-full animate-spin mb-3`} />
        <p className="text-sm">Memuat kategori...</p>
      </div>
    );
  }

  if (categories.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <Hash className="w-12 h-12 mb-3 opacity-30" />
        <p className="text-sm text-center px-4">
          Masukkan diagnosis dan klik "Generate AI Insight" untuk melihat kategori ICD-10
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className={`flex-shrink-0 pb-3 mb-3 border-b ${isDark ? 'border-cyan-500/20' : 'border-blue-200'}`}>
        <h3 className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          Kategori Diagnosis
        </h3>
        <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
          {categories.length} kategori ditemukan
        </p>
      </div>

      {/* Scrollable category list with max height for 6 items */}
      <div className={`space-y-1.5 pr-2 ${
        categories.length > 6 ? 'max-h-[400px] overflow-y-auto' : ''
      } ${
        isDark 
          ? 'scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-slate-800/20' 
          : 'scrollbar-thin scrollbar-thumb-blue-400/40 scrollbar-track-gray-200/40'
      } hover:scrollbar-thumb-cyan-500/50`}>
        {categories.map((category) => (
          <button
            key={category.headCode}
            onClick={() => onSelectCategory(category.headCode)}
            className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 group ${
              selectedHeadCode === category.headCode
                ? isDark
                  ? 'bg-cyan-500/20 border border-cyan-500/50 shadow-md'
                  : 'bg-blue-50 border border-blue-400 shadow-md'
                : isDark
                ? 'bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/50 hover:border-cyan-500/30'
                : 'bg-white/50 border border-gray-200 hover:bg-white hover:border-blue-300'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-3 flex-shrink-0">
                <span
                  className={`text-lg font-bold ${
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
                className={`text-sm font-medium flex-1 min-w-0 ${
                  selectedHeadCode === category.headCode
                    ? isDark ? 'text-slate-200' : 'text-gray-800'
                    : isDark ? 'text-slate-300' : 'text-gray-700'
                }`}
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
            {/* Common term (Istilah Umum) */}
            {category.commonTerm && (
              <div className={`mt-2 px-2 py-1 rounded ${
                selectedHeadCode === category.headCode
                  ? isDark ? 'bg-cyan-500/10 border-l-2 border-cyan-400' : 'bg-blue-50 border-l-2 border-blue-500'
                  : isDark ? 'bg-slate-700/30 border-l-2 border-slate-600' : 'bg-gray-50 border-l-2 border-gray-400'
              }`}>
                <p className={`text-xs font-medium ${
                  selectedHeadCode === category.headCode
                    ? isDark ? 'text-cyan-300' : 'text-blue-700'
                    : isDark ? 'text-slate-400' : 'text-gray-600'
                }`}>
                  {category.commonTerm}
                </p>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
