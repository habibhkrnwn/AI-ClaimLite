import { useState, useEffect, useMemo } from 'react';
import { Pill, Sparkles, ChevronRight, ChevronDown, ChevronUp } from 'lucide-react';

interface MedicationSuggestion {
  kode_fornas: string;
  obat_name: string;
  kelas_terapi: string;
  confidence: number;
}

interface MedicationExplorerProps {
  searchTerm: string;
  normalizedTerm: string;
  suggestions: MedicationSuggestion[];
  isDark: boolean;
  onMedicationSelected?: (code: string, name: string) => void;
}

interface TherapeuticGroup {
  kelas_terapi: string;
  medications: MedicationSuggestion[];
  count: number;
  maxConfidence: number;
}

export default function MedicationExplorer({
  searchTerm,
  normalizedTerm,
  suggestions,
  isDark,
  onMedicationSelected,
}: MedicationExplorerProps) {
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Group suggestions by therapeutic class (like ICD hierarchy)
  const therapeuticGroups = useMemo<TherapeuticGroup[]>(() => {
    const groupMap = new Map<string, MedicationSuggestion[]>();

    suggestions.forEach((suggestion) => {
      const kelas = suggestion.kelas_terapi || 'Lainnya';
      if (!groupMap.has(kelas)) {
        groupMap.set(kelas, []);
      }
      groupMap.get(kelas)!.push(suggestion);
    });

    return Array.from(groupMap.entries())
      .map(([kelas_terapi, medications]) => ({
        kelas_terapi,
        medications: medications.sort((a, b) => b.confidence - a.confidence),
        count: medications.length,
        maxConfidence: Math.max(...medications.map((m) => m.confidence)),
      }))
      .sort((a, b) => b.maxConfidence - a.maxConfidence); // Sort groups by highest confidence
  }, [suggestions]);

  // Auto-select first suggestion and auto-expand first group
  useEffect(() => {
    if (suggestions.length > 0 && !selectedCode) {
      const firstSuggestion = suggestions[0];
      setSelectedCode(firstSuggestion.kode_fornas);
      onMedicationSelected?.(firstSuggestion.kode_fornas, firstSuggestion.obat_name);
      
      // Auto-expand first group
      if (therapeuticGroups.length > 0) {
        setExpandedGroups(new Set([therapeuticGroups[0].kelas_terapi]));
      }
    }
  }, [suggestions, therapeuticGroups]);

  const handleSelectSuggestion = (suggestion: MedicationSuggestion) => {
    setSelectedCode(suggestion.kode_fornas);
    onMedicationSelected?.(suggestion.kode_fornas, suggestion.obat_name);
  };

  const toggleGroup = (kelas_terapi: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(kelas_terapi)) {
        next.delete(kelas_terapi);
      } else {
        next.add(kelas_terapi);
      }
      return next;
    });
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header with AI Translation Info */}
      <div className={`p-4 rounded-lg ${
        isDark ? 'bg-cyan-500/10 border border-cyan-500/30' : 'bg-blue-50 border border-blue-200'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className={`w-4 h-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <span className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            AI Translation (FORNAS)
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>
            {searchTerm}
          </span>
          <ChevronRight className="w-4 h-4" />
          <span className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            {normalizedTerm}
          </span>
        </div>
      </div>

      {/* Suggestions List */}
      <div className={`flex-1 rounded-lg p-4 ${
        isDark ? 'bg-slate-800/50 border border-slate-700/50' : 'bg-white/50 border border-gray-200'
      }`}>
        <div className="flex flex-col h-full">
          <div className={`flex-shrink-0 pb-3 mb-3 border-b ${isDark ? 'border-cyan-500/20' : 'border-blue-200'}`}>
            <h3 className={`text-sm font-semibold flex items-center gap-2 ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              <Pill className="w-4 h-4" />
              Saran Obat FORNAS
            </h3>
            <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
              {suggestions.length} obat ditemukan
            </p>
          </div>

          {/* Scrollable grouped medications - Max 5 items visible */}
          <div className={`space-y-2 pr-2 overflow-y-auto ${
            isDark 
              ? 'scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-slate-800/20' 
              : 'scrollbar-thin scrollbar-thumb-blue-400/40 scrollbar-track-gray-200/40'
          } hover:scrollbar-thumb-cyan-500/50`}
          style={{ height: '280px', maxHeight: '280px' }}>
            {suggestions.length === 0 ? (
              <div className={`flex flex-col items-center justify-center py-12 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
                <Pill className="w-12 h-12 mb-3 opacity-30" />
                <p className="text-sm text-center">
                  Tidak ada obat ditemukan di FORNAS
                </p>
              </div>
            ) : (
              therapeuticGroups.map((group) => (
                <div key={group.kelas_terapi} className="space-y-1">
                  {/* Group Header (Therapeutic Class) */}
                  <button
                    onClick={() => toggleGroup(group.kelas_terapi)}
                    className={`w-full px-3 py-2 rounded-md flex items-center justify-between transition-all duration-200 ${
                      isDark
                        ? 'bg-gradient-to-r from-cyan-500/10 to-cyan-500/5 border border-cyan-500/30 hover:border-cyan-500/50'
                        : 'bg-gradient-to-r from-blue-50 to-blue-50/50 border border-blue-300 hover:border-blue-400'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Pill className={`w-4 h-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
                      <span className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                        {group.kelas_terapi}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        isDark ? 'bg-cyan-500/20 text-cyan-300' : 'bg-blue-100 text-blue-700'
                      }`}>
                        {group.count}
                      </span>
                    </div>
                    {expandedGroups.has(group.kelas_terapi) ? (
                      <ChevronUp className={`w-4 h-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
                    ) : (
                      <ChevronDown className={`w-4 h-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
                    )}
                  </button>

                  {/* Medications in Group */}
                  {expandedGroups.has(group.kelas_terapi) && (
                    <div className="space-y-1 pl-2">
                      {group.medications.map((suggestion) => (
                        <button
                          key={suggestion.kode_fornas}
                          onClick={() => handleSelectSuggestion(suggestion)}
                          className={`w-full rounded-md transition-all duration-200 text-left ${
                            selectedCode === suggestion.kode_fornas
                              ? isDark
                                ? 'bg-cyan-500/20 border-2 border-cyan-500/50 shadow-lg shadow-cyan-500/20'
                                : 'bg-blue-50 border-2 border-blue-400 shadow-lg shadow-blue-500/10'
                              : isDark
                              ? 'bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/50 hover:border-cyan-500/30'
                              : 'bg-white/50 border border-gray-200 hover:bg-white hover:border-blue-300'
                          }`}
                          style={{ minHeight: '55px' }}
                        >
                          <div className="px-3 py-2 flex flex-col gap-1">
                            {/* Code and Confidence Badge */}
                            <div className="flex items-center justify-between gap-2">
                              <span className={`text-xs font-bold ${
                                selectedCode === suggestion.kode_fornas
                                  ? isDark ? 'text-cyan-300' : 'text-blue-700'
                                  : isDark ? 'text-cyan-400' : 'text-blue-600'
                              }`}>
                                {suggestion.kode_fornas}
                              </span>
                              {suggestion.confidence >= 95 && (
                                <span className={`text-xs px-2 py-0.5 rounded ${
                                  isDark ? 'bg-green-500/20 text-green-300' : 'bg-green-100 text-green-700'
                                }`}>
                                  ✓ Match
                                </span>
                              )}
                            </div>

                            {/* Medication Name */}
                            <p className={`text-sm font-medium leading-tight ${
                              selectedCode === suggestion.kode_fornas
                                ? isDark ? 'text-slate-200' : 'text-gray-800'
                                : isDark ? 'text-slate-300' : 'text-gray-700'
                            }`}>
                              {suggestion.obat_name}
                            </p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
