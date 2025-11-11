import { useState, useEffect } from 'react';
import InputPanel from './InputPanel';
import ResultsPanel from './ResultsPanel';
import { AnalysisResult } from '../lib/supabase';
import { apiService } from '../lib/api';

type InputMode = 'form' | 'text';

interface AdminRSDashboardProps {
  isDark: boolean;
}

export default function AdminRSDashboard({ isDark }: AdminRSDashboardProps) {
  const [inputMode, setInputMode] = useState<InputMode>('form');
  const [diagnosis, setDiagnosis] = useState('');
  const [procedure, setProcedure] = useState('');
  const [medication, setMedication] = useState('');
  const [freeText, setFreeText] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [aiUsage, setAiUsage] = useState<{ used: number; remaining: number; limit: number } | null>(null);

  // Load AI usage on component mount
  useEffect(() => {
    loadAIUsage();
  }, []);

  const loadAIUsage = async () => {
    try {
      console.log('[AdminRS] Loading AI usage...');
      const response = await apiService.getAIUsageStatus();
      console.log('[AdminRS] getAIUsageStatus response:', response);
      if (response.success) {
        console.log('[AdminRS] Setting aiUsage to:', response.data);
        setAiUsage(response.data);
      } else {
        console.error('[AdminRS] Failed to load usage - response not successful');
      }
    } catch (error) {
      console.error('[AdminRS] Failed to load AI usage:', error);
    }
  };

  const handleGenerate = async () => {
    setIsLoading(true);
    try {
      // Prepare request data based on input mode
      const requestData = inputMode === 'text' 
        ? { mode: 'text' as const, input_text: freeText }
        : { mode: 'form' as const, diagnosis, procedure, medication };

      // Call AI Analysis API
      const response = await apiService.analyzeClaimAI(requestData);

      if (response.success) {
        // Update AI usage from response
        if (response.usage) {
          console.log('[AdminRS] Received usage from API:', response.usage);
          setAiUsage({
            used: response.usage.used,
            remaining: response.usage.remaining,
            limit: response.usage.limit,
          });
          console.log('[AdminRS] Updated aiUsage state');
        } else {
          console.warn('[AdminRS] No usage data in response');
        }

        // Transform API response to match AnalysisResult interface
        const aiResult = response.data;
        
        // Map severity from AI result
        let severityLevel: 'ringan' | 'sedang' | 'berat' = 'sedang';
        const severityTingkat = aiResult.severity?.tingkat?.toLowerCase();
        if (severityTingkat === 'mild' || severityTingkat === 'ringan') {
          severityLevel = 'ringan';
        } else if (severityTingkat === 'severe' || severityTingkat === 'berat') {
          severityLevel = 'berat';
        }

        // Map validation status
        let validationStatus: 'valid' | 'warning' | 'invalid' = 'valid';
        const validStatus = aiResult.validasi_klinis?.status?.toLowerCase();
        if (validStatus === 'invalid' || validStatus === 'tidak valid') {
          validationStatus = 'invalid';
        } else if (validStatus === 'warning' || validStatus === 'peringatan') {
          validationStatus = 'warning';
        }

        // Map Fornas status
        let fornasStatus: 'sesuai' | 'tidak-sesuai' | 'perlu-review' = 'sesuai';
        const fornasKepatuhan = aiResult.fornas?.tingkat_kepatuhan || 100;
        if (fornasKepatuhan < 50) {
          fornasStatus = 'tidak-sesuai';
        } else if (fornasKepatuhan < 80) {
          fornasStatus = 'perlu-review';
        }
        
        const analysisResult: AnalysisResult = {
          classification: {
            icd10: aiResult.klasifikasi?.icd10 ? [aiResult.klasifikasi.icd10] : [],
            icd9: aiResult.klasifikasi?.icd9 ? 
              (Array.isArray(aiResult.klasifikasi.icd9) ? aiResult.klasifikasi.icd9 : [aiResult.klasifikasi.icd9]) 
              : [],
          },
          validation: {
            status: validationStatus,
            message: aiResult.validasi_klinis?.keterangan || aiResult.insight_ai || 'Analisis berhasil',
          },
          severity: severityLevel,
          cpNasional: aiResult.cp_ringkas?.map((item: any) => 
            `${item.nama_tindakan}: ${item.tarif_ringkas}`
          ).join(', ') || '-',
          requiredDocs: aiResult.checklist_dokumen?.map((doc: any) => doc.nama_dokumen) || [],
          fornas: {
            status: fornasStatus,
            message: `Kepatuhan: ${fornasKepatuhan}% - ${aiResult.fornas?.catatan || 'Sesuai standar'}`,
          },
          aiInsight: aiResult.insight_ai || 'Analisis berhasil dilakukan.',
          consistency: aiResult.konsistensi?.skor_keseluruhan || 85,
        };

        setResult(analysisResult);

        // Log the analysis
        try {
          const logData = inputMode === 'text'
            ? { diagnosis: freeText, procedure: '', medication: '' }
            : { diagnosis, procedure, medication };
          
          await apiService.logAnalysis(logData);
        } catch (logError) {
          console.error('Failed to log analysis:', logError);
        }
      } else {
        throw new Error('Analysis failed');
      }
    } catch (error: any) {
      console.error('Analysis failed:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Gagal melakukan analisis';
      
      // Check if it's a limit exceeded error
      if (error.response?.status === 429) {
        alert(`Limit penggunaan AI harian Anda sudah habis!\n\nSilakan coba lagi besok atau hubungi admin untuk menambah limit.`);
      } else {
        alert(`Error: ${errorMessage}\n\nPastikan core_engine API sedang berjalan di port 8000.`);
      }
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
