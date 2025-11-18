import { Sparkles } from 'lucide-react';

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

interface SharedMappingPreviewProps {
  isDark: boolean;
  isAnalyzing: boolean;
  icd10Code?: { code: string; name: string } | null;
  icd9Code?: { code: string; name: string } | null;
  originalDiagnosis?: string;
  originalProcedure?: string;
  originalMedication?: string;
  selectedMedicationCategory?: MedicationCategory | null;
  selectedMedicationDetails?: string[];
  onGenerateAnalysis?: () => void;
}

export default function SharedMappingPreview({
  isDark,
  isAnalyzing,
  icd10Code,
  icd9Code,
  originalDiagnosis,
  originalProcedure,
  originalMedication,
  selectedMedicationCategory,
  selectedMedicationDetails = [],
  onGenerateAnalysis,
}: SharedMappingPreviewProps) {
  const hasSelection = icd10Code || icd9Code;
  
  // Get selected medication detail object
  const selectedMedicationDetail = selectedMedicationCategory && selectedMedicationDetails.length > 0
    ? selectedMedicationCategory.details.find(d => d.kode_fornas === selectedMedicationDetails[0])
    : null;

  return (
    <div className={`rounded-lg p-4 ${
      isDark ? 'bg-slate-800/50 border border-slate-700/50' : 'bg-white/50 border border-gray-200'
    }`}>
      <h3 className={`text-sm font-semibold mb-3 ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
        Preview Mapping
      </h3>
      
      {hasSelection ? (
        <div className="space-y-4">
          {/* ICD-10 Diagnosis Mapping */}
          {icd10Code && (
            <div className={`p-4 rounded-lg ${isDark ? 'bg-slate-700/50' : 'bg-blue-50'}`}>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                🩺 Diagnosis (Original)
              </label>
              <p className={`text-sm mb-3 ${isDark ? 'text-slate-400 line-through' : 'text-gray-500 line-through'}`}>
                {originalDiagnosis || '-'}
              </p>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                ICD-10 Code ✓
              </label>
              {/* Highlight dengan ukuran lebih besar */}
              <div className={`p-4 rounded-lg border-2 ${
                isDark 
                  ? 'bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border-cyan-400 shadow-lg shadow-cyan-500/20' 
                  : 'bg-gradient-to-br from-blue-100 to-cyan-100 border-blue-400 shadow-lg shadow-blue-500/20'
              }`}>
                <div className={`font-bold text-2xl mb-2 ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                  {icd10Code.code}
                </div>
                <div className={`text-sm leading-relaxed ${isDark ? 'text-cyan-100' : 'text-blue-900'}`}>
                  {icd10Code.name}
                </div>
              </div>
            </div>
          )}

          {/* ICD-9 Procedure Mapping */}
          {icd9Code && (
            <div className={`p-4 rounded-lg ${isDark ? 'bg-slate-700/50' : 'bg-green-50'}`}>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                ⚕️ Tindakan (Original)
              </label>
              <p className={`text-sm mb-3 ${isDark ? 'text-slate-400 line-through' : 'text-gray-500 line-through'}`}>
                {originalProcedure || '-'}
              </p>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-green-300' : 'text-green-700'}`}>
                ICD-9 Code ✓
              </label>
              {/* Highlight dengan ukuran lebih besar */}
              <div className={`p-4 rounded-lg border-2 ${
                isDark 
                  ? 'bg-gradient-to-br from-green-500/20 to-emerald-500/20 border-green-400 shadow-lg shadow-green-500/20' 
                  : 'bg-gradient-to-br from-green-100 to-emerald-100 border-green-400 shadow-lg shadow-green-500/20'
              }`}>
                <div className={`font-bold text-2xl mb-2 ${isDark ? 'text-green-300' : 'text-green-700'}`}>
                  {icd9Code.code}
                </div>
                <div className={`text-sm leading-relaxed ${isDark ? 'text-green-100' : 'text-green-900'}`}>
                  {icd9Code.name}
                </div>
              </div>
            </div>
          )}

          {/* Medication/Obat - Show selected detail */}
          {selectedMedicationDetail ? (
            <div className={`p-4 rounded-lg ${isDark ? 'bg-slate-700/50' : 'bg-purple-50'}`}>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                💊 Obat (Original)
              </label>
              <p className={`text-sm mb-3 ${isDark ? 'text-slate-400 line-through' : 'text-gray-500 line-through'}`}>
                {originalMedication || '-'}
              </p>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                FORNAS Obat ✓
              </label>
              {/* Highlight dengan format: Generic Name - Sediaan */}
              <div className={`p-4 rounded-lg border-2 ${
                isDark 
                  ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 border-purple-400 shadow-lg shadow-purple-500/20' 
                  : 'bg-gradient-to-br from-purple-100 to-pink-100 border-purple-400 shadow-lg shadow-purple-500/20'
              }`}>
                <div className={`font-bold text-xl mb-2 ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                  {selectedMedicationCategory?.generic_name} - {selectedMedicationDetail.sediaan_kekuatan}
                </div>
                {selectedMedicationDetail.restriksi_penggunaan && (
                  <div className={`text-xs mt-2 p-2 rounded ${
                    isDark ? 'bg-orange-500/20 text-orange-300' : 'bg-orange-100 text-orange-700'
                  }`}>
                    ⚠️ {selectedMedicationDetail.restriksi_penggunaan}
                  </div>
                )}
              </div>
            </div>
          ) : originalMedication && (
            <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-700/50' : 'bg-purple-50'}`}>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                💊 Obat
              </label>
              <div className={`p-2 rounded border ${isDark ? 'bg-purple-500/10 border-purple-500/30 text-purple-300' : 'bg-purple-100 border-purple-300 text-purple-700'}`}>
                <div className={`text-sm ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                  {originalMedication}
                  <span className="block text-xs mt-1 opacity-70">Pilih sediaan untuk mapping</span>
                </div>
              </div>
            </div>
          )}

          {/* Generate Analysis Button */}
          {icd10Code && (
            <button
              onClick={onGenerateAnalysis}
              disabled={isAnalyzing}
              className={`w-full py-3 px-4 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 ${
                isAnalyzing
                  ? isDark
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : isDark
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white shadow-lg'
                    : 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white shadow-lg'
              }`}
            >
              {isAnalyzing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate AI Analysis</span>
                </>
              )}
            </button>
          )}
        </div>
      ) : (
        <div className={`text-center py-8 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
          <svg className="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-xs">Pilih kode ICD untuk melihat preview mapping</p>
        </div>
      )}
    </div>
  );
}
