// STEP-BY-STEP: Add History Tab to AdminRSDashboard.tsx

// ============================================
// STEP 1: Update imports (at top of file)
// ============================================
import { useState, useEffect } from 'react';
import InputPanel from './InputPanel';
import ResultsPanel from './ResultsPanel';
import AnalysisHistory from './AnalysisHistory';  // ← ADD THIS
import { AnalysisResult } from '../lib/supabase';
import { apiService } from '../lib/api';

type InputMode = 'form' | 'text';
type TabMode = 'analysis' | 'history';  // ← ADD THIS

interface AdminRSDashboardProps {
  isDark: boolean;
  user?: any;  // ← ADD THIS
}

// ============================================
// STEP 2: Add tabMode state (after line 18)
// ============================================
export default function AdminRSDashboard({ isDark, user }: AdminRSDashboardProps) {
  const [tabMode, setTabMode] = useState<TabMode>('analysis');  // ← ADD THIS
  const [inputMode, setInputMode] = useState<InputMode>('form');
  // ... rest of states

// ============================================
// STEP 3: Replace return statement (starting at line 194)
// ============================================
// DELETE: return ( <div className="h-full flex gap-4"> ...
// REPLACE WITH:

return (
  <div className="h-full flex flex-col gap-4">
    {/* Tab Navigation */}
    <div className="flex-shrink-0 bg-transparent">
      <div className="flex space-x-2">
        <button
          onClick={() => setTabMode('analysis')}
          className={`px-6 py-3 font-medium rounded-t-lg transition-colors ${
            tabMode === 'analysis'
              ? isDark
                ? 'bg-slate-800/40 text-cyan-400 border-b-2 border-cyan-500'
                : 'bg-white/60 text-blue-600 border-b-2 border-blue-600'
              : isDark
              ? 'bg-slate-800/20 text-gray-400 hover:text-gray-300 hover:bg-slate-800/30'
              : 'bg-white/30 text-gray-600 hover:text-gray-800 hover:bg-white/40'
          }`}
        >
          📊 Analisis Baru
        </button>
        <button
          onClick={() => setTabMode('history')}
          className={`px-6 py-3 font-medium rounded-t-lg transition-colors ${
            tabMode === 'history'
              ? isDark
                ? 'bg-slate-800/40 text-cyan-400 border-b-2 border-cyan-500'
                : 'bg-white/60 text-blue-600 border-b-2 border-blue-600'
              : isDark
              ? 'bg-slate-800/20 text-gray-400 hover:text-gray-300 hover:bg-slate-800/30'
              : 'bg-white/30 text-gray-600 hover:text-gray-800 hover:bg-white/40'
          }`}
        >
          📋 Riwayat Analisis
        </button>
      </div>
    </div>

    {/* Tab Content */}
    <div className="flex-1 overflow-hidden">
      {tabMode === 'analysis' ? (
        // Analysis Tab (existing UI)
        <div className="h-full flex gap-4">
          {/* Left Panel - Input */}
          <div className="w-72 flex-shrink-0">
            <div
              className={`rounded-2xl p-6 h-full ${
                isDark
                  ? 'bg-slate-800/40 border border-cyan-500/20'
                  : 'bg-white/60 border border-blue-100'
              } backdrop-blur-xl shadow-2xl flex flex-col`}
            >
              <h2
                className={`text-lg font-semibold mb-2 flex-shrink-0 ${
                  isDark ? 'text-cyan-300' : 'text-blue-700'
                }`}
              >
                Smart Input Hybrid
              </h2>

              {/* AI Usage Indicator */}
              {aiUsage && (
                <div className={`mb-4 p-3 rounded-lg flex-shrink-0 ${
                  isDark ? 'bg-slate-700/50 border border-cyan-500/20' : 'bg-blue-50/80 border border-blue-200'
                }`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                      AI Usage Today
                    </span>
                    <span className={`text-xs font-bold ${
                      aiUsage.remaining === 0 
                        ? 'text-red-500' 
                        : aiUsage.remaining < 10 
                        ? 'text-yellow-500' 
                        : isDark ? 'text-cyan-400' : 'text-blue-600'
                    }`}>
                      {aiUsage.used}/{aiUsage.limit}
                    </span>
                  </div>
                  <div className={`w-full h-2 rounded-full ${isDark ? 'bg-slate-600' : 'bg-gray-200'}`}>
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        aiUsage.remaining === 0 
                          ? 'bg-red-500' 
                          : aiUsage.remaining < 10 
                          ? 'bg-yellow-500' 
                          : 'bg-gradient-to-r from-cyan-500 to-blue-500'
                      }`}
                      style={{ width: `${(aiUsage.used / aiUsage.limit) * 100}%` }}
                    />
                  </div>
                  <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
                    {aiUsage.remaining} requests remaining
                  </p>
                </div>
              )}

              <div className="flex gap-2 mb-4 flex-shrink-0">
                <button
                  onClick={() => {
                    setInputMode('form');
                    setFreeText('');
                  }}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all duration-300 ${
                    inputMode === 'form'
                      ? isDark
                        ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/50'
                        : 'bg-blue-200 text-blue-700 border border-blue-400'
                      : isDark
                      ? 'bg-slate-700/30 text-slate-300 border border-slate-600/30 hover:bg-slate-700/50'
                      : 'bg-white/30 text-gray-600 border border-gray-300/30 hover:bg-white/50'
                  }`}
                >
                  Form Input
                </button>
                <button
                  onClick={() => {
                    setInputMode('text');
                    setDiagnosis('');
                    setProcedure('');
                    setMedication('');
                  }}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all duration-300 ${
                    inputMode === 'text'
                      ? isDark
                        ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/50'
                        : 'bg-blue-200 text-blue-700 border border-blue-400'
                      : isDark
                      ? 'bg-slate-700/30 text-slate-300 border border-slate-600/30 hover:bg-slate-700/50'
                      : 'bg-white/30 text-gray-600 border border-gray-300/30 hover:bg-white/50'
                  }`}
                >
                  Free Text
                </button>
              </div>

              <div className="flex-1 min-h-0">
                <InputPanel
                  mode={inputMode}
                  diagnosis={diagnosis}
                  procedure={procedure}
                  medication={medication}
                  freeText={freeText}
                  onDiagnosisChange={setDiagnosis}
                  onProcedureChange={setProcedure}
                  onMedicationChange={setMedication}
                  onFreeTextChange={setFreeText}
                  onGenerate={handleGenerate}
                  isLoading={isLoading}
                  isDark={isDark}
                  aiUsage={aiUsage}
                />
              </div>
            </div>
          </div>

          {/* Right Panel - Results */}
          <div className="flex-1 overflow-hidden">
            <div
              className={`rounded-2xl p-6 h-full ${
                isDark
                  ? 'bg-slate-800/40 border border-cyan-500/20'
                  : 'bg-white/60 border border-blue-100'
              } backdrop-blur-xl shadow-2xl flex flex-col overflow-hidden`}
            >
              <h2
                className={`text-lg font-semibold mb-6 flex-shrink-0 ${
                  isDark ? 'text-cyan-300' : 'text-blue-700'
                }`}
              >
                Hasil Analisis AI
              </h2>
              <div className="flex-1 overflow-y-auto">
                <ResultsPanel result={result} isDark={isDark} />
              </div>
            </div>
          </div>
        </div>
      ) : (
        // History Tab (NEW!)
        <div
          className={`rounded-2xl p-6 h-full ${
            isDark
              ? 'bg-slate-800/40 border border-cyan-500/20'
              : 'bg-white/60 border border-blue-100'
          } backdrop-blur-xl shadow-2xl overflow-hidden`}
        >
          <AnalysisHistory 
            userId={user?.id} 
            isAdmin={false}
          />
        </div>
      )}
    </div>
  </div>
);
