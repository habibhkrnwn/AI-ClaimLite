import { useState } from 'react';
import InputPanel from './InputPanel';
import ResultsPanel from './ResultsPanel';
import { generateAIAnalysis } from '../lib/mockAI';
import { AnalysisResult } from '../lib/supabase';
import { apiService } from '../lib/api';

type InputMode = 'text' | 'excel';

interface AdminRSDashboardProps {
  isDark: boolean;
}

export default function AdminRSDashboard({ isDark }: AdminRSDashboardProps) {
  const [inputMode, setInputMode] = useState<InputMode>('text');
  const [diagnosis, setDiagnosis] = useState('');
  const [procedure, setProcedure] = useState('');
  const [medication, setMedication] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerate = async () => {
    setIsLoading(true);
    try {
      const analysisResult = await generateAIAnalysis(diagnosis, procedure, medication);
      setResult(analysisResult);

      // Log the analysis
      try {
        await apiService.logAnalysis({
          diagnosis,
          procedure,
          medication,
        });
      } catch (logError) {
        console.error('Failed to log analysis:', logError);
        // Continue even if logging fails
      }
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex gap-4">
      {/* Left Panel - Fixed Width */}
      <div className="w-72 flex-shrink-0">
        <div
          className={`rounded-2xl p-6 h-full ${
            isDark
              ? 'bg-slate-800/40 border border-cyan-500/20'
              : 'bg-white/60 border border-blue-100'
          } backdrop-blur-xl shadow-2xl flex flex-col overflow-hidden`}
        >
          <h2
            className={`text-lg font-semibold mb-4 ${
              isDark ? 'text-cyan-300' : 'text-blue-700'
            }`}
          >
            Smart Input Hybrid
          </h2>

          <div className="flex gap-2 mb-6 flex-shrink-0">
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
              Text Input
            </button>
            <button
              onClick={() => {
                setInputMode('excel');
                setDiagnosis('');
                setProcedure('');
                setMedication('');
              }}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all duration-300 ${
                inputMode === 'excel'
                  ? isDark
                    ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/50'
                    : 'bg-blue-200 text-blue-700 border border-blue-400'
                  : isDark
                  ? 'bg-slate-700/30 text-slate-300 border border-slate-600/30 hover:bg-slate-700/50'
                  : 'bg-white/30 text-gray-600 border border-gray-300/30 hover:bg-white/50'
              }`}
            >
              Excel Import
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            <InputPanel
              mode={inputMode}
              diagnosis={diagnosis}
              procedure={procedure}
              medication={medication}
              onDiagnosisChange={setDiagnosis}
              onProcedureChange={setProcedure}
              onMedicationChange={setMedication}
              onGenerate={handleGenerate}
              isLoading={isLoading}
              isDark={isDark}
            />
          </div>
        </div>
      </div>

      {/* Right Panel - Single Full Results Card */}
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
  );
}
