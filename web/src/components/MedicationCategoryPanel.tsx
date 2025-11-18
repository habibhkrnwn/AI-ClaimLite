import React from 'react';
import { Pill, ChevronRight, AlertCircle } from 'lucide-react';

interface MedicationCategory {
  generic_name: string;
  kelas_terapi: string;
  sub_kelas_terapi: string;
  total_dosage_forms: number;
  confidence: number;
  details: Array<{
    kode_fornas: string;
    obat_name: string;
    sediaan_kekuatan: string;
  }>;
}

interface MedicationCategoryPanelProps {
  categories: MedicationCategory[];
  selectedCategory: MedicationCategory | null;
  onSelectCategory: (category: MedicationCategory) => void;
  isLoading: boolean;
}

const MedicationCategoryPanel: React.FC<MedicationCategoryPanelProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  isLoading,
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-200">
        <Pill className="w-5 h-5 text-green-600" />
        <h3 className="font-semibold text-gray-800">Obat Utama (Generic)</h3>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mb-2"></div>
            <p className="text-sm text-gray-600 animate-pulse">Memuat kategori obat...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && categories.length === 0 && (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <AlertCircle className="w-12 h-12 text-yellow-500 mb-3 animate-bounce" />
          <p className="text-sm text-gray-600 mb-1">Tidak ada obat ditemukan</p>
          <p className="text-xs text-gray-400">Coba kata kunci yang berbeda atau periksa ejaan</p>
          <div className="mt-2 px-3 py-1 bg-yellow-50 border border-yellow-200 rounded-full">
            <span className="text-xs text-yellow-700 font-medium">⚠️ Tidak Ada Hasil</span>
          </div>
        </div>
      )}

      {/* Category List */}
      {!isLoading && categories.length > 0 && (
        <div className="space-y-2 overflow-y-auto" style={{ maxHeight: '280px' }}>
          {categories.map((category, index) => {
            const isSelected = selectedCategory?.generic_name === category.generic_name;
            const isHighConfidence = category.confidence >= 95;

            return (
              <button
                key={index}
                onClick={() => onSelectCategory(category)}
                className={`w-full text-left p-3 rounded-lg border transition-all ${
                  isSelected
                    ? 'bg-green-50 border-green-300 shadow-sm'
                    : 'bg-gray-50 border-gray-200 hover:bg-green-50 hover:border-green-200'
                }`}
                style={{ minHeight: '55px' }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-800 text-sm">
                        {category.generic_name}
                      </span>
                      {isHighConfidence && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                          ✓ Match
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-600">
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded">
                        {category.kelas_terapi || 'Tidak Diketahui'}
                      </span>
                      <span className="text-gray-400">•</span>
                      <span>{category.total_dosage_forms} sediaan</span>
                    </div>
                  </div>
                  <ChevronRight
                    className={`w-5 h-5 transition-transform ${
                      isSelected ? 'text-green-600 transform rotate-90' : 'text-gray-400'
                    }`}
                  />
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MedicationCategoryPanel;
