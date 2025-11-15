import { useState, useEffect } from 'react';
import { Sparkles, ChevronRight } from 'lucide-react';
import ICD9CategoryPanel, { ICD9Category } from './ICD9CategoryPanel';
import ICD9DetailPanel from './ICD9DetailPanel';

interface ICD9ExplorerProps {
  searchTerm: string;
  correctedTerm: string;
  synonyms?: string[];
  originalInput: {
    diagnosis?: string;
    procedure?: string;
    medication?: string;
    freeText?: string;
    mode: 'form' | 'text';
  };
  isDark: boolean;
  isAnalyzing?: boolean;
  hidePreview?: boolean;
  onCodeSelected?: (code: string, name: string) => void;
  onGenerateAnalysis?: () => void;
}

export default function ICD9Explorer({
  searchTerm,
  correctedTerm,
  synonyms = [],
  originalInput,
  isDark,
  isAnalyzing = false,
  hidePreview = false,
  onCodeSelected,
  onGenerateAnalysis,
}: ICD9ExplorerProps) {
  const [icd9Categories, setIcd9Categories] = useState<ICD9Category[]>([]);
  const [selectedHeadCode, setSelectedHeadCode] = useState<string | null>(null);
  const [selectedDetails, setSelectedDetails] = useState<Array<{code: string; name: string}>>([]);
  const [selectedSubCode, setSelectedSubCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (correctedTerm) {
      loadICD9Hierarchy();
    }
  }, [correctedTerm, synonyms]);

  const loadICD9Hierarchy = async () => {
    setIsLoading(true);
    try {
      const { apiService } = await import('../lib/api');
      const response = await apiService.getICD9Hierarchy(correctedTerm, synonyms);
      
      if (response.success && response.data.categories.length > 0) {
        setIcd9Categories(response.data.categories);
        
        // Auto-select first category
        const firstCategory = response.data.categories[0];
        setSelectedHeadCode(firstCategory.headCode);
        setSelectedDetails(firstCategory.details || []);
        
        // If no specific sub-codes, auto-select HEAD code as mapping
        if (!firstCategory.details || firstCategory.details.length === 0) {
          setSelectedSubCode(firstCategory.headCode);
          onCodeSelected?.(firstCategory.headCode, firstCategory.headName);
        }
      }
    } catch (error) {
      // Silent error handling
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectCategory = (headCode: string) => {
    setSelectedHeadCode(headCode);
    const category = icd9Categories.find(c => c.headCode === headCode);
    if (category && category.details) {
      setSelectedDetails(category.details);
      
      // If no specific sub-codes, auto-select HEAD code as mapping
      if (category.details.length === 0) {
        setSelectedSubCode(headCode);
        onCodeSelected?.(headCode, category.headName);
      } else {
        // Reset subcode selection when changing category
        setSelectedSubCode(null);
      }
    } else {
      // Reset subcode selection when changing category
      setSelectedSubCode(null);
    }
  };

  const handleSelectSubCode = (code: string, name: string) => {
    setSelectedSubCode(code);
    // Notify parent component
    onCodeSelected?.(code, name);
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header with Correction Info */}
      <div className={`p-4 rounded-lg ${
        isDark ? 'bg-cyan-500/10 border border-cyan-500/30' : 'bg-blue-50 border border-blue-200'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className={`w-4 h-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <span className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            AI Translation (Tindakan)
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>
            {searchTerm}
          </span>
          <ChevronRight className="w-4 h-4" />
          <span className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            {correctedTerm}
          </span>
        </div>
        
        {/* Selected Code Indicator */}
        {selectedSubCode && (
          <div className={`mt-3 pt-3 border-t ${isDark ? 'border-cyan-500/20' : 'border-blue-200'}`}>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                Selected:
              </span>
              <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                isDark 
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' 
                  : 'bg-blue-100 text-blue-700 border border-blue-300'
              }`}>
                ✓ {selectedSubCode}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Layout: Categories | Details (or + Preview if not hidden) */}
      <div className={hidePreview ? "grid grid-cols-2 gap-4 items-start" : "grid grid-cols-3 gap-4 items-start"}>
        {/* Column 1: ICD-9 Categories (Left) */}
        <div className={`rounded-lg p-4 ${
          isDark ? 'bg-slate-800/50 border border-slate-700/50' : 'bg-white/50 border border-gray-200'
        }`}>
          <ICD9CategoryPanel
            categories={icd9Categories}
            selectedHeadCode={selectedHeadCode}
            onSelectCategory={handleSelectCategory}
            isDark={isDark}
            isLoading={isLoading}
          />
        </div>

        {/* Column 2: ICD-9 Details (Middle) */}
        <div className={`rounded-lg p-4 ${
          isDark ? 'bg-slate-800/50 border border-slate-700/50' : 'bg-white/50 border border-gray-200'
        }`}>
          <ICD9DetailPanel
            headCode={selectedHeadCode}
            details={selectedDetails}
            isDark={isDark}
            isLoading={false}
            selectedCode={selectedSubCode}
            onSelectCode={handleSelectSubCode}
          />
        </div>

        {/* Column 3: Mapping Preview (Right) - Only if not hidden */}
        {!hidePreview && (
        <div className={`rounded-lg p-4 ${
          isDark ? 'bg-slate-800/50 border border-slate-700/50' : 'bg-white/50 border border-gray-200'
        }`}>
          <h3 className={`text-sm font-semibold mb-3 ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            Preview Mapping (Tindakan)
          </h3>
          
          {selectedSubCode ? (
            <div className="space-y-4">
              {/* Tindakan Mapping */}
              <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-700/50' : 'bg-blue-50'}`}>
                <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                  Tindakan (Original)
                </label>
                <p className={`text-sm mb-2 ${isDark ? 'text-slate-400 line-through' : 'text-gray-500 line-through'}`}>
                  {originalInput.mode === 'text' ? originalInput.freeText : originalInput.procedure}
                </p>
                <label className={`text-xs font-medium block mb-2 ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                  Tindakan (Medical Term)
                </label>
                <div className={`p-2 rounded border ${isDark ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300' : 'bg-blue-100 border-blue-300 text-blue-700'}`}>
                  <div className="font-bold text-sm">{selectedSubCode}</div>
                  <div className="text-xs mt-1">
                    {(() => {
                      // Try to find in selectedDetails first (for sub-codes)
                      const detail = selectedDetails.find(d => d.code === selectedSubCode);
                      if (detail) return detail.name;
                      
                      // If not found, it's a HEAD code - find in categories
                      const category = icd9Categories.find(c => c.headCode === selectedSubCode);
                      if (category) return category.headName;
                      
                      // Fallback to corrected term
                      return correctedTerm;
                    })()}
                  </div>
                </div>
              </div>

              {/* Info */}
              <div className={`p-3 rounded-lg ${isDark ? 'bg-amber-500/10 border border-amber-500/30' : 'bg-amber-50 border border-amber-200'}`}>
                <div className="flex items-start gap-2">
                  <span className="text-amber-500 text-lg">💡</span>
                  <div>
                    <p className={`text-xs font-medium mb-1 ${isDark ? 'text-amber-300' : 'text-amber-700'}`}>
                      Preview Mapping
                    </p>
                    <p className={`text-xs ${isDark ? 'text-amber-200/80' : 'text-amber-600'}`}>
                      Tindakan akan menggunakan kode <strong>{selectedSubCode}</strong> untuk analisis AI.
                    </p>
                  </div>
                </div>
              </div>

              {/* Generate AI Analysis Button */}
              <button
                onClick={onGenerateAnalysis}
                disabled={isAnalyzing}
                className={`w-full py-3 px-4 rounded-lg font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 ${
                  isAnalyzing
                    ? isDark
                      ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : isDark
                    ? 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20'
                    : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg'
                }`}
              >
                {isAnalyzing ? (
                  <>
                    <div className={`w-4 h-4 border-2 ${isDark ? 'border-slate-500 border-t-slate-300' : 'border-gray-400 border-t-gray-600'} rounded-full animate-spin`} />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Generate AI Analysis ({selectedSubCode})</span>
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
              <svg className="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-sm text-center px-4">
                Pilih sub-kode ICD-9 untuk melihat preview mapping
              </p>
            </div>
          )}
        </div>
        )}
      </div>
    </div>
  );
}
