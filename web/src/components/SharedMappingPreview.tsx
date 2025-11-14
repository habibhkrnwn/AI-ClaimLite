import { Sparkles } from 'lucide-react';

interface SharedMappingPreviewProps {
  isDark: boolean;
  isAnalyzing: boolean;
  icd10Code?: { code: string; name: string } | null;
  icd9Code?: { code: string; name: string } | null;
  originalDiagnosis?: string;
  originalProcedure?: string;
  originalMedication?: string;
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
  onGenerateAnalysis,
}: SharedMappingPreviewProps) {
  const hasSelection = icd10Code || icd9Code;

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
            <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-700/50' : 'bg-blue-50'}`}>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                🩺 Diagnosis (Original)
              </label>
              <p className={`text-sm mb-2 ${isDark ? 'text-slate-400 line-through' : 'text-gray-500 line-through'}`}>
                {originalDiagnosis || '-'}
              </p>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                ICD-10 Code
              </label>
              <div className={`p-2 rounded border ${isDark ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300' : 'bg-blue-100 border-blue-300 text-blue-700'}`}>
                <div className="font-bold text-sm">{icd10Code.code}</div>
                <div className="text-xs mt-1">{icd10Code.name}</div>
              </div>
            </div>
          )}

          {/* ICD-9 Procedure Mapping */}
          {icd9Code && (
            <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-700/50' : 'bg-green-50'}`}>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                ⚕️ Tindakan (Original)
              </label>
              <p className={`text-sm mb-2 ${isDark ? 'text-slate-400 line-through' : 'text-gray-500 line-through'}`}>
                {originalProcedure || '-'}
              </p>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-green-300' : 'text-green-700'}`}>
                ICD-9 Code
              </label>
              <div className={`p-2 rounded border ${isDark ? 'bg-green-500/10 border-green-500/30 text-green-300' : 'bg-green-100 border-green-300 text-green-700'}`}>
                <div className="font-bold text-sm">{icd9Code.code}</div>
                <div className="text-xs mt-1">{icd9Code.name}</div>
              </div>
            </div>
          )}

          {/* Medication/Obat */}
          {originalMedication && (
            <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-700/50' : 'bg-purple-50'}`}>
              <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                💊 Obat
              </label>
              <div className={`p-2 rounded border ${isDark ? 'bg-purple-500/10 border-purple-500/30 text-purple-300' : 'bg-purple-100 border-purple-300 text-purple-700'}`}>
                <div className="text-sm">{originalMedication}</div>
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
