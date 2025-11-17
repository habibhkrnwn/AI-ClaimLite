import { useState, useEffect } from 'react';
import SmartInputPanel from './SmartInputPanel';
import ICD10Explorer from './ICD10Explorer';
import ICD9Explorer from './ICD9Explorer';
import SharedMappingPreview from './SharedMappingPreview';
import ResultsPanel from './ResultsPanel';
//import AnalysisHistory from './AnalysisHistory';
import { AnalysisResult } from '../lib/supabase';
import { apiService } from '../lib/api';

type InputMode = 'form' | 'text';
//type TabMode = 'analysis' | 'history';

interface AdminRSDashboardProps {
  isDark: boolean;
  user?: any;
}

export default function AdminRSDashboard({ isDark }: AdminRSDashboardProps) {
  //const [tabMode, setTabMode] = useState<TabMode>('analysis');
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
      const response = await apiService.getAIUsageStatus();
      if (response.success) {
        setAiUsage(response.data);
      }
    } catch (error) {
      // Silent error handling
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
    
    try {
      // Run translations in parallel for speed
      const procedureTerm = inputMode === 'text' ? '' : procedure;
      setOriginalProcedureTerm(procedureTerm || '');

      const promises: Promise<any>[] = [];
      if (inputTerm) {
        promises.push(apiService.translateMedicalTerm(inputTerm));
      } else {
        promises.push(Promise.resolve(null));
      }
      if (procedureTerm) {
        promises.push(apiService.translateProcedureTerm(procedureTerm));
      } else {
        promises.push(Promise.resolve(null));
      }

      const [dxResp, pxResp] = await Promise.all(promises);

      // Handle diagnosis translation
      if (inputTerm) {
        if (dxResp && dxResp.success) {
          const medicalTerm = dxResp.data.translated;
          setCorrectedTerm(medicalTerm);
        } else {
          setCorrectedTerm(inputTerm);
        }
        setShowICD10Explorer(true);
      }

      // Handle procedure translation
      if (procedureTerm) {
        if (pxResp && pxResp.success) {
          const medicalProcedureTerm = pxResp.data.translated;
          const synonyms = pxResp.data.synonyms || [medicalProcedureTerm];
          setCorrectedProcedureTerm(medicalProcedureTerm);
          setProcedureSynonyms(synonyms);
        } else {
          setCorrectedProcedureTerm(procedureTerm);
          setProcedureSynonyms([procedureTerm]);
        }
        setShowICD9Explorer(true);
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
    const startTime = Date.now();
    
    try {
      // Prepare request data based on input mode
      const requestData = inputMode === 'text' 
        ? { 
            mode: 'text' as const, 
            input_text: freeText,
            icd10_code: selectedICD10Code.code,
            icd9_code: selectedICD9Code?.code || null,
            use_optimized: true,
            save_history: true
          }
        : { 
            mode: 'form' as const, 
            diagnosis, 
            procedure, 
            medication,
            icd10_code: selectedICD10Code.code,
            icd9_code: selectedICD9Code?.code || null,
            use_optimized: true,
            save_history: true
          };

      console.log('[Generate Analysis] Request data:', requestData);
      console.log('[Generate Analysis] Starting analysis at', new Date().toISOString());

      // Call AI Analysis API
      const response = await apiService.analyzeClaimAI(requestData);
      
      const processingTime = Date.now() - startTime;
      console.log(`[Generate Analysis] Completed in ${processingTime}ms`);

      if (response.success) {
        // Update AI usage from response
        if (response.usage) {
          setAiUsage({
            used: response.usage.used,
            remaining: response.usage.remaining,
            limit: response.usage.limit,
          });
        }

        // Transform API response to match AnalysisResult interface
        const aiResult = response.data;
        
        // Use selected ICD-10 code instead of auto-detected
        const icd10Code = selectedICD10Code.code; // Use user-selected code
        
        // Extract ICD-9 codes from tindakan array (NEW FORMAT)
        const tindakanArray = aiResult.klasifikasi?.tindakan || [];
        const icd9Codes = tindakanArray
          .map((t: any) => {
            // New format: tindakan is array of objects with icd9 property
            if (typeof t === 'object' && t.icd9 && t.icd9 !== '-') {
              return t.icd9;
            }
            // Old format fallback: extract from string pattern
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
        const cpRingkasList = Array.isArray(aiResult.cp_ringkas)
          ? aiResult.cp_ringkas.map((item: any) => {
              if (typeof item === 'string') {
                return { tahap: '', keterangan: item };
              }
              return {
                tahap: item.tahap || item.stage_name || '',
                keterangan: item.keterangan || item.description || '',
              };
            })
          : [];

        
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
          // severity: severityLevel,
          cpNasional: cpRingkasList,
          requiredDocs: requiredDocs,
          fornas: {
            status: fornasStatus,
            message: `${sesuaiCount}/${totalObat} obat sesuai Fornas (${Math.round(fornasPercentage)}%)`,
          },
          // ⬇️ TAMBAHKAN INI
          fornasList: aiResult.fornas_validation || [],
          fornasSummary: aiResult.fornas_summary || {},
          aiInsight: aiResult.insight_ai || 'Analisis berhasil dilakukan.',
          consistency: {
            dx_tx: aiResult.konsistensi?.dx_tx || {},
            dx_drug: aiResult.konsistensi?.dx_drug || {},
            tx_drug: aiResult.konsistensi?.tx_drug || {},
            tingkat: aiResult.konsistensi?.tingkat_konsistensi || "-",
            score: Number(aiResult.konsistensi?._score) || 0
          },
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
      const processingTime = Date.now() - startTime;
      
      console.error('Analysis failed after', processingTime, 'ms');
      console.error('Error object:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      
      const errorMessage = error.response?.data?.message || error.message || 'Gagal melakukan analisis';
      const errorDetail = error.response?.data?.detail || '';
      const errorCode = error.response?.data?.error_code || error.code;
      const statusCode = error.response?.status;
      
      // Check specific error types
      if (statusCode === 429) {
        // Limit exceeded
        alert(`⚠️ Limit penggunaan AI harian Anda sudah habis!\n\nSilakan coba lagi besok atau hubungi admin untuk menambah limit.`);
      } else if (statusCode === 504 || errorCode === 'ECONNABORTED') {
        // Timeout error
        alert(
          `⏱️ Analisis Timeout (${Math.round(processingTime / 1000)} detik)\n\n` +
          `Penyebab umum:\n` +
          `• OpenAI API sedang lambat\n` +
          `• Core engine sedang sibuk\n` +
          `• Data terlalu kompleks\n\n` +
          `💡 Solusi:\n` +
          `• Tunggu 10-30 detik, lalu coba lagi\n` +
          `• Pastikan koneksi internet stabil\n` +
          `• Coba simplify input data\n\n` +
          `Jika masih error, hubungi admin.`
        );
      } else if (statusCode === 503 || errorCode === 'ECONNREFUSED') {
        // Core engine not running
        alert(
          `🔌 Tidak dapat terhubung ke Core Engine\n\n` +
          `Core Engine tidak berjalan atau tidak dapat diakses.\n` +
          `Pastikan Core Engine berjalan di port 8000.\n\n` +
          `Hubungi administrator untuk memulai layanan.`
        );
      } else {
        // Generic error
        let fullErrorMessage = `❌ Error: ${errorMessage}`;
        
        if (errorDetail) {
          fullErrorMessage += `\n\n📝 Detail: ${errorDetail}`;
        }
        
        if (errorCode) {
          fullErrorMessage += `\n\n🔍 Error Code: ${errorCode}`;
        }
        
        fullErrorMessage += `\n\n⏱️ Processing Time: ${Math.round(processingTime / 1000)} detik`;
        fullErrorMessage += `\n\n💡 Tip: Pastikan Core Engine berjalan di port 8000`;
        
        alert(fullErrorMessage);
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
                {/* ================== Hasil Analisis AI ================== */}
                <div
                  className={`rounded-xl p-4 mb-4 ${
                    isDark
                      ? "bg-cyan-500/10 border border-cyan-500/30"
                      : "bg-blue-50 border border-blue-200"
                  }`}
                >
                  {/* HEADER: Judul + ICD di kanan */}
                  <div className="flex items-center justify-between mb-2">

                    {/* LEFT: Judul + Deskripsi */}
                    <div>
                      <h3
                        className={`text-base font-semibold ${
                          isDark ? "text-cyan-300" : "text-blue-700"
                        }`}
                      >
                        📊 Hasil Analisis AI
                      </h3>
                      <p
                        className={`text-xs ${
                          isDark ? "text-slate-400" : "text-gray-600"
                        }`}
                      >
                        Analisis lengkap berdasarkan input dan kode ICD-10 yang dipilih
                      </p>
                    </div>

                    {/* RIGHT: ICD-10 & ICD-9 (Horizontal, Highlight) */}
                    <div className="flex items-center gap-4">

                      {/* ICD-10 */}
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs ${
                            isDark ? "text-slate-400" : "text-gray-500"
                          }`}
                        >
                          ICD-10
                        </span>

                        <span
                          className={`
                            text-lg font-bold font-mono tracking-wide
                            px-3 py-1 rounded-lg
                            ${isDark ? "bg-cyan-500/20 text-cyan-300" : "bg-blue-100 text-blue-700"}
                          `}
                        >
                          {result?.classification?.icd10?.[0] ?? "-"}
                        </span>
                      </div>

                      {/* Divider */}
                      <span className={`${isDark ? "text-slate-600" : "text-gray-400"}`}>
                        |
                      </span>

                      {/* ICD-9 */}
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs ${
                            isDark ? "text-slate-400" : "text-gray-500"
                          }`}
                        >
                          ICD-9
                        </span>

                        <span
                          className={`
                            text-lg font-bold font-mono tracking-wide
                            px-3 py-1 rounded-lg
                            ${isDark ? "bg-blue-500/20 text-blue-300" : "bg-blue-100 text-blue-700"}
                          `}
                        >
                          {result?.classification?.icd9?.[0] ?? "-"}
                        </span>
                      </div>
                    </div>
                  </div>
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
