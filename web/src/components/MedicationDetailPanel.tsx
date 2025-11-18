import React from 'react';
import { Package } from 'lucide-react';

interface MedicationDetail {
  kode_fornas: string;
  obat_name: string;
  sediaan_kekuatan: string;
  restriksi_penggunaan?: string;
}

interface MedicationCategory {
  generic_name: string;
  kelas_terapi: string;
  subkelas_terapi: string;
  total_dosage_forms: number;
  confidence: number;
  details: MedicationDetail[];
}

interface MedicationDetailPanelProps {
  category: MedicationCategory | null;
  selectedDetails: string[];
  onToggleDetail: (kodeFornas: string) => void;
  isDark: boolean;
  isLoading?: boolean;
}

const MedicationDetailPanel: React.FC<MedicationDetailPanelProps> = ({
  category,
  selectedDetails,
  onToggleDetail,
  isDark,
  isLoading = false,
}) => {
  // Show empty state if no category selected
  if (!category) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <Package className="w-12 h-12 mb-3 opacity-30" />
        <p className="text-sm text-center">
          Pilih obat utama untuk melihat sediaan
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <div className={`w-8 h-8 border-3 ${isDark ? 'border-green-500/30 border-t-green-500' : 'border-green-500/30 border-t-green-500'} rounded-full animate-spin mb-3`} />
        <p className="text-sm">Memuat detail...</p>
      </div>
    );
  }

  if (category.details.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
        <Package className="w-12 h-12 mb-3 opacity-30" />
        <p className="text-sm text-center px-4">
          Tidak ada sediaan untuk {category.generic_name}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className={`flex-shrink-0 pb-3 mb-3 border-b ${isDark ? 'border-green-500/20' : 'border-green-200'}`}>
        <h3 className={`text-sm font-semibold ${isDark ? 'text-green-300' : 'text-green-700'}`}>
          Sediaan Obat: {category.generic_name}
        </h3>
        <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
          {category.details.length} sediaan tersedia
        </p>
      </div>

      {/* Details list with fixed height and scroll - Max 5 items visible */}
      <div className={`space-y-1.5 pr-2 overflow-y-auto ${
        isDark 
          ? 'scrollbar-thin scrollbar-thumb-green-500/30 scrollbar-track-slate-800/20' 
          : 'scrollbar-thin scrollbar-thumb-green-400/40 scrollbar-track-gray-200/40'
      } hover:scrollbar-thumb-green-500/50`}
      style={{ height: '280px', maxHeight: '280px' }}>
        {category.details.map((detail, index) => {
          const isSelected = selectedDetails.includes(detail.kode_fornas);

          return (
            <button
              key={detail.kode_fornas || `medication-${index}`}
              onClick={() => onToggleDetail(detail.kode_fornas)}
              className={`w-full rounded-md transition-all duration-200 text-left ${
                isSelected
                  ? isDark
                    ? 'bg-green-500/20 border-2 border-green-500/50 shadow-lg shadow-green-500/20'
                    : 'bg-green-50 border-2 border-green-400 shadow-lg shadow-green-500/10'
                  : isDark
                  ? 'bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/50 hover:border-green-500/30'
                  : 'bg-white/50 border border-gray-200 hover:bg-white hover:border-green-300'
              }`}
              style={{ minHeight: '55px', maxHeight: '80px' }}
            >
              <div className="h-full px-2.5 py-2 flex items-center gap-2 overflow-hidden">
                <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-semibold ${
                  isSelected
                    ? isDark ? 'bg-green-500/30 text-green-300' : 'bg-green-100 text-green-700'
                    : isDark ? 'bg-green-500/20 text-green-300' : 'bg-green-100 text-green-700'
                }`}>
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0 overflow-y-auto max-h-full">
                  <div className="flex items-center gap-2 flex-wrap flex-shrink-0">
                    <span
                      className={`text-xs font-mono flex-shrink-0 px-1.5 py-0.5 rounded ${
                        isSelected
                          ? isDark ? 'bg-green-500/30 text-green-200' : 'bg-green-100 text-green-700'
                          : isDark ? 'bg-slate-700/50 text-slate-400' : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {detail.kode_fornas}
                    </span>
                  </div>
                  <p
                    className={`text-sm font-medium mt-1 truncate ${
                      isSelected
                        ? isDark ? 'text-slate-200' : 'text-gray-800'
                        : isDark ? 'text-slate-300' : 'text-gray-700'
                    }`}
                    title={detail.obat_name}
                  >
                    {detail.sediaan_kekuatan}
                  </p>
                  {detail.restriksi_penggunaan && (
                    <p className={`text-xs mt-0.5 truncate ${
                      isDark ? 'text-orange-300' : 'text-orange-600'
                    }`}>
                      ⚠️ {detail.restriksi_penggunaan}
                    </p>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Summary - Changed to singular text */}
      {selectedDetails.length > 0 && (
        <div className={`flex-shrink-0 mt-3 pt-3 border-t ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
          <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
            <span className={`font-medium ${isDark ? 'text-green-400' : 'text-green-600'}`}>
              1
            </span>{' '}
            sediaan dipilih
          </p>
        </div>
      )}
    </div>
  );
};

export default MedicationDetailPanel;
