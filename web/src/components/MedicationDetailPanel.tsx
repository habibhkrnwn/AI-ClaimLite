import React from 'react';
import { Package, Check } from 'lucide-react';

interface MedicationDetail {
  kode_fornas: string;
  obat_name: string;
  sediaan_kekuatan: string;
}

interface MedicationCategory {
  generic_name: string;
  kelas_terapi: string;
  sub_kelas_terapi: string;
  total_dosage_forms: number;
  confidence: number;
  details: MedicationDetail[];
}

interface MedicationDetailPanelProps {
  category: MedicationCategory | null;
  selectedDetails: string[];
  onToggleDetail: (kodeFornas: string) => void;
}

const MedicationDetailPanel: React.FC<MedicationDetailPanelProps> = ({
  category,
  selectedDetails,
  onToggleDetail,
}) => {
  if (!category) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-200">
          <Package className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-800">Sediaan Obat (Turunan)</h3>
        </div>
        <div className="flex items-center justify-center py-12 text-center">
          <p className="text-sm text-gray-400">Pilih obat utama untuk melihat sediaan</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-200">
        <Package className="w-5 h-5 text-blue-600" />
        <div className="flex-1">
          <h3 className="font-semibold text-gray-800">Sediaan Obat (Turunan)</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {category.generic_name} • {category.total_dosage_forms} sediaan tersedia
          </p>
        </div>
      </div>

      {/* Details List */}
      <div className="space-y-2 overflow-y-auto" style={{ maxHeight: '280px' }}>
        {category.details.map((detail, index) => {
          const isSelected = selectedDetails.includes(detail.kode_fornas);

          return (
            <button
              key={index}
              onClick={() => onToggleDetail(detail.kode_fornas)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                isSelected
                  ? 'bg-blue-50 border-blue-300 shadow-sm'
                  : 'bg-gray-50 border-gray-200 hover:bg-blue-50 hover:border-blue-200'
              }`}
              style={{ minHeight: '55px' }}
            >
              <div className="flex items-start gap-3">
                {/* Checkbox */}
                <div
                  className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                    isSelected
                      ? 'bg-blue-600 border-blue-600'
                      : 'bg-white border-gray-300'
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3 text-white" />}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                      {detail.kode_fornas}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-gray-800 mb-1">
                    {detail.sediaan_kekuatan}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {detail.obat_name}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Summary */}
      {selectedDetails.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-600">
            <span className="font-medium text-blue-600">{selectedDetails.length}</span>{' '}
            sediaan dipilih
          </p>
        </div>
      )}
    </div>
  );
};

export default MedicationDetailPanel;
