import { useState, useEffect } from 'react';
import SmartInputPanel from './SmartInputPanel';
import ICD10Explorer from './ICD10Explorer';
import ICD9Explorer from './ICD9Explorer';
import SharedMappingPreview from './SharedMappingPreview';
import ResultsPanel from './ResultsPanel';
import AnalysisHistory from './AnalysisHistory';
import { AnalysisResult } from '../lib/supabase';
import { apiService } from '../lib/api';

type InputMode = 'form' | 'text';
type TabMode = 'analysis' | 'history';

interface AdminRSDashboardProps {
  isDark: boolean;
  user?: any;
}

export default function AdminRSDashboard({ isDark, user }: AdminRSDashboardProps) {
  const [tabMode, setTabMode] = useState<TabMode>('analysis');
  const [inputMode, setInputMode] = useState<InputMode>('form');
  const [diagnosis, setDiagnosis] = useState('');
  const [procedure, setProcedure] = useState('');
  const [medication, setMedication] = useState('');
  const [freeText, setFreeText] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [aiUsage, setAiUsage] = useState<{ used: number; remaining: number; limit: number } | null>(null);
  
  // ICD-10 Explorer state (Diagnosis)
  const [showICD10Explorer, setShowICD10Explorer] = useState(false);
  const [correctedTerm, setCorrectedTerm] = useState('');
  const [originalSearchTerm, setOriginalSearchTerm] = useState('');
  const [selectedICD10Code, setSelectedICD10Code] = useState<{code: string; name: string} | null>(null);

  // ICD-9 Explorer state (Procedure/Tindakan)
  const [showICD9Explorer, setShowICD9Explorer] = useState(false);
  const [correctedProcedureTerm, setCorrectedProcedureTerm] = useState('');
  const [procedureSynonyms, setProcedureSynonyms] = useState<string[]>([]);
  const [originalProcedureTerm, setOriginalProcedureTerm] = useState('');
  const [selectedICD9Code, setSelectedICD9Code] = useState<{code: string; name: string} | null>(null);

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
    
    // Reset previous state when generating new search
    setShowICD10Explorer(false);
    setShowICD9Explorer(false);
    setResult(null);
    setSelectedICD10Code(null);
    setSelectedICD9Code(null);
    
    // Prepare AI correction for diagnosis
    const inputTerm = inputMode === 'text' ? freeText : diagnosis;
    setOriginalSearchTerm(inputTerm);
    
    console.log('[DEBUG] Input term:', inputTerm);
    console.log('[DEBUG] Input mode:', inputMode);
    
    try {
      // Step 1: Translate diagnosis to medical term using OpenAI
      if (inputTerm) {
        console.log('[ICD-10] Translating term:', inputTerm);
        const translationResponse = await apiService.translateMedicalTerm(inputTerm);
        
        console.log('[DEBUG] Translation response:', translationResponse);
        
        if (translationResponse.success) {
          const medicalTerm = translationResponse.data.translated;
          console.log('[ICD-10] Translated to:', medicalTerm);
          setCorrectedTerm(medicalTerm);
          setShowICD10Explorer(true);
          console.log('[DEBUG] Setting showICD10Explorer to TRUE');
          console.log('[DEBUG] Setting correctedTerm to:', medicalTerm);
        } else {
          console.error('[ICD-10] Translation failed');
          // Fallback to original term
          setCorrectedTerm(inputTerm);
          setShowICD10Explorer(true);
          console.log('[DEBUG] Fallback - Setting showICD10Explorer to TRUE');
        }
      }
      
      // Step 2: Translate procedure if provided
      const procedureTerm = inputMode === 'text' ? '' : procedure;
      if (procedureTerm) {
        setOriginalProcedureTerm(procedureTerm);
        console.log('[ICD-9] Translating procedure term:', procedureTerm);
        
        const procedureTranslation = await apiService.translateProcedureTerm(procedureTerm);
        
        console.log('[DEBUG] Procedure translation response:', procedureTranslation);
        
        if (procedureTranslation.success) {
          const medicalProcedureTerm = procedureTranslation.data.translated;
          const synonyms = procedureTranslation.data.synonyms || [medicalProcedureTerm];
          console.log('[ICD-9] Translated to:', medicalProcedureTerm);
          console.log('[ICD-9] Synonyms:', synonyms);
          setCorrectedProcedureTerm(medicalProcedureTerm);
          setProcedureSynonyms(synonyms);
          setShowICD9Explorer(true);
        } else {
          console.error('[ICD-9] Translation failed');
          setCorrectedProcedureTerm(procedureTerm);
          setProcedureSynonyms([procedureTerm]);
          setShowICD9Explorer(true);
        }
      }
      
    } catch (error: any) {
      console.error('[Translation] Error:', error);
      
      // Show user-friendly error message
      const errorMessage = error?.response?.data?.message 
        || error?.message 
        || 'Terjadi kesalahan saat melakukan analisis. Silakan coba lagi.';
      
      alert(`Error: ${errorMessage}`);
      
      // Fallback to original terms if translation fails
      if (inputTerm) {
        setCorrectedTerm(inputTerm);
        setShowICD10Explorer(true);
      }
      const procedureTerm = inputMode === 'text' ? '' : procedure;
      if (procedureTerm) {
        setCorrectedProcedureTerm(procedureTerm);
        setShowICD9Explorer(true);
      }
      console.log('[DEBUG] Error fallback - Setting explorers to TRUE');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Generate AI Analysis after code selection
  const handleGenerateAnalysis = async () => {
    if (!selectedICD10Code) {
      alert('Silakan pilih kode ICD-10 terlebih dahulu');
      return;
    }
    
    setIsLoading(true);
    try {
      // Prepare request data based on input mode
      const requestData = inputMode === 'text' 
        ? { 
            mode: 'text' as const, 
            input_text: freeText,
            icd10_code: selectedICD10Code.code,
            icd9_code: selectedICD9Code?.code || null
          }
        : { 
            mode: 'form' as const, 
            diagnosis, 
            procedure, 
            medication,
            icd10_code: selectedICD10Code.code,
            icd9_code: selectedICD9Code?.code || null
          };

      console.log('[AdminRS] Sending analysis request with codes:', {
        icd10: selectedICD10Code.code,
        icd9: selectedICD9Code?.code || 'none'
      });

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
        
        // Use selected ICD-10 code instead of auto-detected
        const icd10Code = selectedICD10Code.code; // Use user-selected code
        
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

  // Handle ICD-10 code selection (just store, don't analyze yet)
  const handleCodeSelection = (code: string, name: string) => {
    setSelectedICD10Code({ code, name });
    console.log(`[ICD-10] Selected: ${code} - ${name}`);
  };

  const handleProcedureCodeSelection = (code: string, name: string) => {
    setSelectedICD9Code({ code, name });
    console.log(`[ICD-9] Selected: ${code} - ${name}`);
  };

  return (
    <div className="h-full flex gap-4">
      {/* Left Panel - Input (Fixed Width) */}
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
            <SmartInputPanel
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

      {/* Right Panel - Scrollable with ICD-10 Explorer + Results */}
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
            Pilih Kode Spesifik ICD-10
          </h2>
          
          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto space-y-6">
            {/* Debug Info */}
            <div className="text-xs text-yellow-500 mb-2">
              DEBUG: showICD10Explorer={String(showICD10Explorer)}, correctedTerm={correctedTerm || 'null'}, showICD9Explorer={String(showICD9Explorer)}, correctedProcedureTerm={correctedProcedureTerm || 'null'}
            </div>
            
            {/* Combined ICD Explorer Section (Diagnosis + Tindakan) */}
            {(showICD10Explorer && correctedTerm) || (showICD9Explorer && correctedProcedureTerm) ? (
              <div className="flex-shrink-0">
                <div className={`mb-4 px-4 py-3 rounded-lg ${
                  isDark ? 'bg-gradient-to-r from-cyan-500/10 to-green-500/10 border border-cyan-500/30' : 'bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200'
                }`}>
                  <h3 className={`text-sm font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                    🏥 Mapping Kode ICD
                  </h3>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                    {showICD10Explorer && showICD9Explorer 
                      ? 'Pilih kode diagnosis (ICD-10) dan tindakan (ICD-9) yang sesuai'
                      : showICD10Explorer 
                        ? 'Pilih kode diagnosis (ICD-10) yang sesuai'
                        : 'Pilih kode tindakan (ICD-9) yang sesuai'
                    }
                  </p>
                </div>

                {/* 2-Column Layout: Explorers (Left 65%) | Shared Mapping Preview (Right 35%) */}
                <div className="grid grid-cols-12 gap-4">
                  {/* Left Column: ICD-10 & ICD-9 Explorers (8 columns = ~66%) */}
                  <div className="col-span-8 space-y-6">
                    {/* ICD-10 Diagnosis Section */}
                    {showICD10Explorer && correctedTerm && (
                      <div>
                        <div className={`mb-3 px-3 py-2 rounded-md ${
                          isDark ? 'bg-cyan-500/5 border-l-2 border-cyan-500' : 'bg-blue-50 border-l-2 border-blue-500'
                        }`}>
                          <h4 className={`text-xs font-semibold ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
                            🩺 Diagnosis ICD-10
                          </h4>
                        </div>
                        <ICD10Explorer
                          searchTerm={originalSearchTerm}
                          correctedTerm={correctedTerm}
                          originalInput={{
                            diagnosis,
                            procedure,
                            medication,
                            freeText,
                            mode: inputMode,
                          }}
                          isDark={isDark}
                          isAnalyzing={isLoading}
                          onCodeSelected={handleCodeSelection}
                          hidePreview={true}
                        />
                      </div>
                    )}

                    {/* ICD-9 Tindakan Section */}
                    {showICD9Explorer && correctedProcedureTerm && (
                      <div>
                        <div className={`mb-3 px-3 py-2 rounded-md ${
                          isDark ? 'bg-green-500/5 border-l-2 border-green-500' : 'bg-green-50 border-l-2 border-green-500'
                        }`}>
                          <h4 className={`text-xs font-semibold ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                            ⚕️ Tindakan ICD-9
                          </h4>
                        </div>
                        <ICD9Explorer
                          searchTerm={originalProcedureTerm}
                          correctedTerm={correctedProcedureTerm}
                          synonyms={procedureSynonyms}
                          originalInput={{
                            diagnosis,
                            procedure,
                            medication,
                            freeText,
                            mode: inputMode,
                          }}
                          isDark={isDark}
                          isAnalyzing={isLoading}
                          onCodeSelected={handleProcedureCodeSelection}
                          hidePreview={true}
                        />
                      </div>
                    )}
                  </div>

                  {/* Right Column: Shared Mapping Preview (4 columns = ~33%, Sticky) */}
                  <div className="col-span-4 sticky top-4">
                    <SharedMappingPreview
                      isDark={isDark}
                      isAnalyzing={isLoading}
                      icd10Code={selectedICD10Code}
                      icd9Code={selectedICD9Code}
                      originalDiagnosis={originalSearchTerm}
                      originalProcedure={originalProcedureTerm}
                      originalMedication={medication}
                      onGenerateAnalysis={handleGenerateAnalysis}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className={`flex flex-col items-center justify-center py-20 ${
                isDark ? 'text-slate-400' : 'text-gray-500'
              }`}>
                <svg className="w-16 h-16 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-sm text-center px-4">
                  Klik "Generate AI Insight" untuk melihat kategori ICD yang sesuai dengan diagnosis dan tindakan
                </p>
              </div>
            )}

            {/* Results Section - Below Explorer */}
            {result && (
              <div className="flex-shrink-0">
                <div className={`rounded-xl p-4 mb-4 ${
                  isDark ? 'bg-cyan-500/10 border border-cyan-500/30' : 'bg-blue-50 border border-blue-200'
                }`}>
                  <h3 className={`text-base font-semibold mb-2 ${
                    isDark ? 'text-cyan-300' : 'text-blue-700'
                  }`}>
                    📊 Hasil Analisis AI
                  </h3>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
                    Analisis lengkap berdasarkan input dan kode ICD-10 yang dipilih
                  </p>
                </div>
                <ResultsPanel result={result} isDark={isDark} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
