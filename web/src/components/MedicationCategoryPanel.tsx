import React from 'react';
import { Pill, ChevronRight } from 'lucide-react';

interface MedicationCategory {
  generic_name: string;
  kelas_terapi: string;
  subkelas_terapi: string;
  total_dosage_forms: number;
  confidence: number;
  details: Array<{
    kode_fornas: string;
    obat_name: string;
    sediaan_kekuatan: string;
    restriksi_penggunaan?: string;
  }>;
}

interface MedicationCategoryPanelProps {
  categories: MedicationCategory[];
  selectedCategory: MedicationCategory | null;
  onSelectCategory: (category: MedicationCategory) => void;
  isLoading: boolean;
  isDark: boolean;
}

const MedicationCategoryPanel: React.FC<MedicationCategoryPanelProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  isLoading,
  isDark,
}) => {
  if (isLoading) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <div className={`w-8 h-8 border-3 ${isDark ? 'border-green-500/30 border-t-green-500' : 'border-green-500/30 border-t-green-500'} rounded-full animate-spin mb-3`} />
        <p className="text-sm animate-pulse">Memuat kategori obat...</p>
      </div>
    );
  }

  if (categories.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <div className="relative">
          <Pill className="w-12 h-12 mb-3 opacity-30 animate-bounce" />
          <div className={`absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center ${
            isDark ? 'bg-orange-500/20 text-orange-400' : 'bg-orange-100 text-orange-600'
          }`}>
            <span className="text-xs">!</span>
          </div>
        </div>
        <p className="text-sm text-center px-4 font-medium">
          Tidak ada obat ditemukan
        </p>
        <p className="text-xs text-center px-4 mt-1 opacity-70">
          Coba kata kunci yang berbeda
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className={`flex-shrink-0 pb-3 mb-3 border-b ${isDark ? 'border-green-500/20' : 'border-green-200'}`}>
        <h3 className={`text-sm font-semibold ${isDark ? 'text-green-300' : 'text-green-700'}`}>
          Obat Utama (Generic)
        </h3>
        <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
          {categories.length} obat ditemukan
        </p>
      </div>

      {/* Scrollable category list with fixed height - Max 5 items visible (5 x 55px = 275px) */}
      <div className={`space-y-1 pr-2 overflow-y-auto ${
        isDark 
          ? 'scrollbar-thin scrollbar-thumb-green-500/30 scrollbar-track-slate-800/20' 
          : 'scrollbar-thin scrollbar-thumb-green-400/40 scrollbar-track-gray-200/40'
      } hover:scrollbar-thumb-green-500/50`}
      style={{ height: '280px', maxHeight: '280px' }}>
        {categories.map((category, index) => {
          const isSelected = selectedCategory?.generic_name === category.generic_name;

          return (
            <button
              key={index}
              onClick={() => onSelectCategory(category)}
              className={`w-full text-left rounded-md transition-all duration-200 group ${
                isSelected
                  ? isDark
                    ? 'bg-green-500/20 border border-green-500/50 shadow-md'
                    : 'bg-green-50 border border-green-400 shadow-md'
                  : isDark
                  ? 'bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/50 hover:border-green-500/30'
                  : 'bg-white/50 border border-gray-200 hover:bg-white hover:border-green-300'
              }`}
              style={{ height: '55px' }}
            >
              <div className="h-full px-2.5 py-2 flex items-center gap-2.5 overflow-hidden">
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Pill
                    className={`w-4 h-4 ${
                      isSelected
                        ? isDark ? 'text-green-300' : 'text-green-700'
                        : isDark ? 'text-green-400' : 'text-green-600'
                    }`}
                  />
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${
                      isSelected
                        ? isDark ? 'bg-green-500/30 text-green-200' : 'bg-green-100 text-green-700'
                        : isDark ? 'bg-slate-700/50 text-slate-400' : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {category.total_dosage_forms}
                  </span>
                </div>
                <p
                  className={`text-sm font-medium flex-1 min-w-0 truncate ${
                    isSelected
                      ? isDark ? 'text-slate-200' : 'text-gray-800'
                      : isDark ? 'text-slate-300' : 'text-gray-700'
                  }`}
                  title={`${category.generic_name} - ${category.kelas_terapi}`}
                >
                  {category.generic_name}
                </p>
                <ChevronRight
                  className={`flex-shrink-0 w-4 h-4 transition-transform duration-200 ${
                    isSelected
                      ? isDark ? 'text-green-400 rotate-90' : 'text-green-600 rotate-90'
                      : isDark ? 'text-slate-500' : 'text-gray-400'
                  }`}
                />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default MedicationCategoryPanel;
