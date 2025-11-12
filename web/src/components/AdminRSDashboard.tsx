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
        console.log('[AdminRS] Full AI Result:', JSON.stringify(aiResult, null, 2));
        
        // Extract ICD codes from klasifikasi
        const diagnosisText = aiResult.klasifikasi?.diagnosis || '';
        const icd10Match = diagnosisText.match(/\(([A-Z]\d{2}(?:\.\d{1,2})?)\)/);
        const icd10Code = icd10Match ? icd10Match[1] : '';
        
        // Extract ICD-9 codes from tindakan array
        const tindakanArray = aiResult.klasifikasi?.tindakan || [];
        const icd9Codes = tindakanArray
          .map((t: any) => {
            if (typeof t === 'string') {
              const match = t.match(/\((\d{2}\.\d{2})\)/);
              return match ? match[1] : null;
            }
            return null;
          })
          .filter((code: any) => code !== null);

        // Map validation status from validasi_klinis
        let validationStatus: 'valid' | 'warning' | 'invalid' = 'valid';
        const sesuaiCP = aiResult.validasi_klinis?.sesuai_cp;
        const sesuaiFornas = aiResult.validasi_klinis?.sesuai_fornas;
        
        if (sesuaiCP === false || sesuaiFornas === false) {
          validationStatus = 'invalid';
        } else if (sesuaiCP === 'parsial' || sesuaiFornas === 'parsial') {
          validationStatus = 'warning';
        }

        // Extract severity from konsistensi.tingkat (percentage)
        let severityLevel: 'ringan' | 'sedang' | 'berat' = 'sedang';
        const konsistensiTingkat = aiResult.konsistensi?.tingkat || 70;
        if (konsistensiTingkat >= 80) {
          severityLevel = 'ringan';
        } else if (konsistensiTingkat < 60) {
          severityLevel = 'berat';
        }

        // Map Fornas status from fornas_summary
        let fornasStatus: 'sesuai' | 'tidak-sesuai' | 'perlu-review' = 'sesuai';
        const fornasSummary = aiResult.fornas_summary || {};
        const sesuaiCount = fornasSummary.sesuai || 0;
        const totalObat = fornasSummary.total_obat || 1;
        const fornasPercentage = (sesuaiCount / totalObat) * 100;
        
        if (fornasPercentage < 50) {
          fornasStatus = 'tidak-sesuai';
        } else if (fornasPercentage < 80) {
          fornasStatus = 'perlu-review';
        }
        
        // Format CP Ringkas
        const cpRingkasText = Array.isArray(aiResult.cp_ringkas) 
          ? aiResult.cp_ringkas.map((item: any) => {
              if (typeof item === 'string') return item;
              return `${item.tahap || item.stage_name || ''}: ${item.keterangan || item.description || ''}`;
            }).join(' • ')
          : (typeof aiResult.cp_ringkas === 'string' ? aiResult.cp_ringkas : '-');
        
        // Format Required Docs
        const requiredDocs = Array.isArray(aiResult.checklist_dokumen)
          ? aiResult.checklist_dokumen.map((doc: any) => {
              if (typeof doc === 'string') return doc;
              return doc.nama_dokumen || doc.document || doc.name || '';
            }).filter((d: string) => d)
          : [];
        
        const analysisResult: AnalysisResult = {
          classification: {
            icd10: icd10Code ? [icd10Code] : [],
            icd9: icd9Codes,
          },
          validation: {
            status: validationStatus,
            message: aiResult.validasi_klinis?.catatan || 
                    `CP: ${sesuaiCP ? '✓ Sesuai' : '✗ Tidak sesuai'}, Fornas: ${sesuaiFornas ? '✓ Sesuai' : '✗ Tidak sesuai'}`,
          },
          severity: severityLevel,
          cpNasional: cpRingkasText,
          requiredDocs: requiredDocs,
          fornas: {
            status: fornasStatus,
            message: `${sesuaiCount}/${totalObat} obat sesuai Fornas (${Math.round(fornasPercentage)}%)`,
          },
          aiInsight: aiResult.insight_ai || 'Analisis berhasil dilakukan.',
          consistency: aiResult.konsistensi?.tingkat || 85,
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
