import { useState } from 'react';
import { Moon, Sun, Cpu } from 'lucide-react';
import InputPanel from './components/InputPanel';
import ResultsPanel from './components/ResultsPanel';
import { generateAIAnalysis } from './lib/mockAI';
import { AnalysisResult } from './lib/supabase';

type InputMode = 'text' | 'excel';

function App() {
  const [isDark, setIsDark] = useState(true);
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
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className={`fixed inset-0 transition-all duration-500 ${
        isDark
          ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900'
          : 'bg-gradient-to-br from-blue-50 via-white to-blue-50'
      } overflow-hidden`}
    >
      <div
        className={`absolute inset-0 opacity-20 ${
          isDark ? 'bg-grid-cyan' : 'bg-grid-blue'
        }`}
        style={{
          backgroundImage: `radial-gradient(circle, ${isDark ? '#06b6d4' : '#3b82f6'} 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />

      <div className="relative z-10 h-full flex flex-col">
        <header
          className={`${
            isDark
              ? 'bg-gradient-to-r from-slate-800/80 to-slate-900/80 border-b border-cyan-500/20'
              : 'bg-gradient-to-r from-blue-600/90 to-blue-800/90 border-b border-blue-400/30'
          } backdrop-blur-xl shadow-2xl flex-shrink-0`}
        >
          <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className={`p-2 rounded-lg ${
                  isDark ? 'bg-cyan-500/20' : 'bg-white/20'
                } backdrop-blur-sm`}
              >
                <Cpu className={`w-8 h-8 ${isDark ? 'text-cyan-400' : 'text-white'}`} />
              </div>
              <div>
                <h1
                  className={`text-2xl font-bold ${
                    isDark
                      ? 'bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent'
                      : 'text-white'
                  }`}
                >
                  AI-CLAIM Lite
                </h1>
                <p
                  className={`text-sm ${
                    isDark ? 'text-slate-400' : 'text-blue-100'
                  }`}
                >
                  Smart Clinical Analyzer
                </p>
              </div>
            </div>

            <button
              onClick={() => setIsDark(!isDark)}
              className={`p-3 rounded-lg ${
                isDark
                  ? 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400'
                  : 'bg-white/20 hover:bg-white/30 text-white'
              } backdrop-blur-sm transition-all duration-300 hover:scale-110 active:scale-95`}
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-hidden">
          <div className="max-w-7xl mx-auto px-6 py-8 h-full flex flex-col">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 overflow-hidden">
              <div
                className={`rounded-2xl p-6 ${
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

              <div
                className={`rounded-2xl p-6 ${
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
        </main>
      </div>
    </div>
  );
}

export default App;
