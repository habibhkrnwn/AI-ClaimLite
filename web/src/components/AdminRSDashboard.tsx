import { useState, useEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
import { FileText, Pill } from 'lucide-react';
import SmartInputPanel from './SmartInputPanel';
import ICD10Explorer from './ICD10Explorer';
import ICD9Explorer from './ICD9Explorer';
import MedicationCategoryPanel from './MedicationCategoryPanel';
import MedicationDetailPanel from './MedicationDetailPanel';
import SharedMappingPreview from './SharedMappingPreview';
import ResultsPanel from './ResultsPanel';
import INACBGPanel from './INACBGPanel';
//import AnalysisHistory from './AnalysisHistory';
import { AnalysisResult, INACBGResult } from '../lib/supabase';
import { apiService } from '../lib/api';

type InputMode = 'form' | 'text';
type ResultViewMode = 'analysis' | 'inacbg';
//type TabMode = 'analysis' | 'history';

interface AdminRSDashboardProps {
  isDark: boolean;
  user?: any;
}

export default function AdminRSDashboard({ isDark }: AdminRSDashboardProps) {
  //const [tabMode, setTabMode] = useState<TabMode>('analysis');
  const [resultViewMode, setResultViewMode] = useState<ResultViewMode>('analysis');
  const [diagnosis, setDiagnosis] = useState('');
  const [procedure, setProcedure] = useState('');
  const [medication, setMedication] = useState('');
  const [serviceType, setServiceType] = useState('');
  const [bpjsClass, setBpjsClass] = useState('');
  const [freeText, setFreeText] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [inacbgResult, setInacbgResult] = useState<INACBGResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [aiUsage, setAiUsage] = useState<{ used: number; remaining: number; limit: number } | null>(null);
  const [isParsed, setIsParsed] = useState(false); // Track if free text was parsed
  const [showResultAnimation, setShowResultAnimation] = useState(false);
  const [showCategoryAnimation, setShowCategoryAnimation] = useState(false);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  
  // Input mode toggle: 'text' or 'form'
  const [inputMode, setInputMode] = useState<InputMode>('form');

  // === DUMMY PARSER FUNCTION (Temporary) ===
  const parseDummyText = (text: string): { diagnosis: string; tindakan: string; obat: string } => {
    const lowerText = text.toLowerCase();
    
    // Deteksi diagnosis berdasarkan kata kunci
    let diagnosis = '';
    if (lowerText.includes('pneumonia') || lowerText.includes('paru') || lowerText.includes('paru basah')) {
      diagnosis = 'Pneumonia';
    } else if (lowerText.includes('diabetes') || lowerText.includes('gula') || lowerText.includes('dm')) {
      diagnosis = 'Diabetes Mellitus';
    } else if (lowerText.includes('hipertensi') || lowerText.includes('darah tinggi') || lowerText.includes('tensi')) {
      diagnosis = 'Hipertensi';
    } else if (lowerText.includes('demam') || lowerText.includes('panas')) {
      diagnosis = 'Demam';
    } else if (lowerText.includes('diare') || lowerText.includes('mencret')) {
      diagnosis = 'Diare Akut';
    } else if (lowerText.includes('tbc') || lowerText.includes('tuberkulosis') || lowerText.includes('tb')) {
      diagnosis = 'Tuberkulosis Paru';
    } else {
      diagnosis = 'Kondisi Umum';
    }
    
    // Deteksi tindakan
    const tindakanList: string[] = [];
    if (lowerText.includes('rontgen') || lowerText.includes('xray') || lowerText.includes('x-ray') || lowerText.includes('foto thorax')) {
      tindakanList.push('Foto Rontgen Thorax');
    }
    if (lowerText.includes('nebulisasi') || lowerText.includes('nebul')) {
      tindakanList.push('Nebulisasi');
    }
    if (lowerText.includes('infus') || lowerText.includes('iv')) {
      tindakanList.push('Pemasangan Infus');
    }
    if (lowerText.includes('ekg') || lowerText.includes('jantung')) {
      tindakanList.push('Pemeriksaan EKG');
    }
    if (lowerText.includes('lab') || lowerText.includes('darah lengkap') || lowerText.includes('cek darah')) {
      tindakanList.push('Pemeriksaan Laboratorium');
    }
    
    // Deteksi obat
    const obatList: string[] = [];
    if (lowerText.includes('ceftriaxone') || lowerText.includes('antibiotik')) {
      obatList.push('Ceftriaxone injeksi 1g');
    }
    if (lowerText.includes('paracetamol') || lowerText.includes('panadol') || lowerText.includes('penurun panas')) {
      obatList.push('Paracetamol 500mg');
    }
    if (lowerText.includes('amoxicillin') || lowerText.includes('amoxilin')) {
      obatList.push('Amoxicillin 500mg');
    }
    if (lowerText.includes('metformin')) {
      obatList.push('Metformin 500mg');
    }
    if (lowerText.includes('amlodipine') || lowerText.includes('amlodipine')) {
      obatList.push('Amlodipine 5mg');
    }
    if (lowerText.includes('omeprazole')) {
      obatList.push('Omeprazole 20mg');
    }
    
    return {
      diagnosis,
      tindakan: tindakanList.join(', ') || 'Pemeriksaan Umum',
      obat: obatList.join(', ') || 'Simptomatik'
    };
  };
  
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

  // Medication Explorer state (Obat) - ICD-like Hierarchy
  const [showMedicationExplorer, setShowMedicationExplorer] = useState(false);
  const [normalizedMedicationTerm, setNormalizedMedicationTerm] = useState('');
  const [medicationCategories, setMedicationCategories] = useState<any[]>([]);
  const [selectedMedicationCategory, setSelectedMedicationCategory] = useState<any>(null);
  const [selectedMedicationDetails, setSelectedMedicationDetails] = useState<string[]>([]);
  const [originalMedicationTerm, setOriginalMedicationTerm] = useState('');
  const [isMedicationLoading, setIsMedicationLoading] = useState(false);

  // Reset isParsed when freeText changes
  const handleFreeTextChange = (value: string) => {
    setFreeText(value);
    if (isParsed) {
      setIsParsed(false);
      if (inputMode === 'text') {
        setDiagnosis('');
        setProcedure('');
        setMedication('');
        setShowICD10Explorer(false);
        setShowICD9Explorer(false);
        setResult(null);
        setSelectedICD10Code(null);
        setSelectedICD9Code(null);
      }
    }
  };

  const handleDiagnosisChange = (value: string) => {
    setDiagnosis(value);
    if (isParsed) {
      setIsParsed(false);
    }
  };

  const handleProcedureChange = (value: string) => {
    setProcedure(value);
    if (isParsed) {
      setIsParsed(false);
    }
  };

  const handleMedicationChange = (value: string) => {
    setMedication(value);
    if (isParsed) {
      setIsParsed(false);
    }
  };

  const handleInputModeChange = (mode: InputMode) => {
    if (mode === 'text' && isParsed) {
      setDiagnosis('');
      setProcedure('');
      setMedication('');
      setIsParsed(false);
      setShowICD10Explorer(false);
      setShowICD9Explorer(false);
      setResult(null);
      setSelectedICD10Code(null);
      setSelectedICD9Code(null);
    }
    setInputMode(mode);
  };

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
    setShowResultAnimation(false);
    setShowCategoryAnimation(false);
    setSelectedICD10Code(null);
    setSelectedICD9Code(null);
    
    // Declare variables in outer scope for error handling
    let diagnosisToUse = '';
    let procedureToUse = '';
    let inputTerm = '';
    let procedureTerm = '';
    
    try {
      // === STEP 1: Check if using Free Text mode ===
      if (inputMode === 'text' && freeText.trim()) {
        console.log('🔍 Parsing free text untuk auto-fill form...');
        
        // Reset form fields first when parsing new free text
        setDiagnosis('');
        setProcedure('');
        setMedication('');
        
        // DUMMY PARSING - Nanti diganti dengan API call
        const dummyParsedData = parseDummyText(freeText);
        
        // Auto-fill form
        setDiagnosis(String(dummyParsedData.diagnosis || ''));
        setProcedure(String(dummyParsedData.tindakan || ''));
        setMedication(String(dummyParsedData.obat || ''));
        
        setIsParsed(true);
        console.log('✓ Form auto-filled:', dummyParsedData);
        
        // Switch to form input mode to show parsed results
        setInputMode('form');
        
        // Wait a bit for state to update
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // Use parsed data for ICD search
        diagnosisToUse = dummyParsedData.diagnosis;
        procedureToUse = dummyParsedData.tindakan;
      } else {
        // === STEP 2: Using Form Input mode - use form values directly ===
        diagnosisToUse = diagnosis;
        procedureToUse = procedure;
      }
    
      // === STEP 3: Translate & Search ICD ===
      inputTerm = diagnosisToUse;
      setOriginalSearchTerm(inputTerm);
      
      procedureTerm = procedureToUse;
      setOriginalProcedureTerm(procedureTerm || '');
      
      const medicationToUse = inputMode === 'text' ? medication : medication;
      setOriginalMedicationTerm(medicationToUse || '');

      // === NEW FLOW: Using Translate Services (NO DUPLICATE SMART LOOKUP) ===
      const promises: Promise<any>[] = [];
      
      // Translate Medical Term (Diagnosis)
      if (inputTerm) {
        promises.push(apiService.translateMedicalTerm(inputTerm));
      } else {
        promises.push(Promise.resolve(null));
      }
      
      // Translate Procedure Term (ICD-9)
      if (procedureTerm) {
        promises.push(apiService.translateProcedureTerm(procedureTerm));
      } else {
        promises.push(Promise.resolve(null));
      }
      
      // Translate Medication Term (FORNAS)
      if (medicationToUse) {
        setIsMedicationLoading(true);
        promises.push(apiService.translateMedicationTerm(medicationToUse));
      } else {
        promises.push(Promise.resolve(null));
      }

      const [dxResp, pxResp, medResp] = await Promise.all(promises);

      // Handle Medical Term Translation (Diagnosis)
      if (inputTerm && dxResp && dxResp.success) {
        const data = dxResp.data;
        console.log('[AdminRS] Translated Diagnosis Response:', data);
        
        // Translate returns {original, translated, confidence}
        const translatedTerm = data.translated || inputTerm;
        console.log('[AdminRS] Diagnosis translated:', inputTerm, '→', translatedTerm);
        
        // Force synchronous state update to prevent race condition
        flushSync(() => {
          setOriginalSearchTerm(inputTerm);
          setCorrectedTerm(translatedTerm);
        });
        
        // Show explorer after state is guaranteed to update
        setShowICD10Explorer(true);
      }

      // Handle Procedure Term Translation (ICD-9)
      if (procedureTerm && pxResp && pxResp.success) {
        const data = pxResp.data;
        console.log('[AdminRS] Translated Procedure:', data);
        
        // Translate just returns {original, translated, confidence}
        // Set translated term and show ICD-9 Explorer for code selection
        const translatedTerm = data.translated || procedureTerm;
        setCorrectedProcedureTerm(translatedTerm);
        setProcedureSynonyms([translatedTerm]);
        console.log('[AdminRS] Procedure translated:', procedureTerm, '→', translatedTerm);
        setShowICD9Explorer(true);
      }
      
      // Handle Medication Term Translation (FORNAS)
      if (medicationToUse && medResp && medResp.success) {
        const data = medResp.data;
        console.log('[AdminRS] Translated Medication Response:', data);
        
        // Response bisa punya 2 format:
        // 1. Simple: {original, translated, confidence}
        // 2. Full: {original, normalized, categories: [...]}
        
        const translatedTerm = data.normalized || data.translated || medicationToUse;
        setNormalizedMedicationTerm(translatedTerm);
        console.log('[AdminRS] Medication normalized:', medicationToUse, '→', translatedTerm);
        
        // Check if categories already included in translate response
        if (data.categories && data.categories.length > 0) {
          console.log('[AdminRS] Categories found in translate response:', data.categories.length);
          setMedicationCategories(data.categories);
          
          // Auto-select first category
          setSelectedMedicationCategory(data.categories[0]);
          
          setIsMedicationLoading(false);
          setShowMedicationExplorer(true);
        } else {
          console.warn('[AdminRS] No categories in translate response, medication explorer will be empty');
          setMedicationCategories([]);
          setIsMedicationLoading(false);
          setShowMedicationExplorer(true);
        }
      } else if (medicationToUse) {
        // Error or no response
        console.warn('[AdminRS] Medication translation failed or no response');
        setNormalizedMedicationTerm(medicationToUse);
        setMedicationCategories([]);
        setIsMedicationLoading(false);
        setShowMedicationExplorer(false);
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
      if (procedureToUse) {
        setCorrectedProcedureTerm(procedureToUse);
        setShowICD9Explorer(true);
      }
      console.log('[DEBUG] Error fallback - Setting explorers to TRUE');
    } finally {
      setIsLoading(false);
    }
  };

  // Animated reveal when category explorers (ICD-10, ICD-9, FORNAS) are ready
  useEffect(() => {
    const hasAnyExplorer =
      (showICD10Explorer && !!correctedTerm) ||
      (showICD9Explorer && !!correctedProcedureTerm) ||
      (showMedicationExplorer && !!normalizedMedicationTerm);

    if (!hasAnyExplorer) return;

    setShowCategoryAnimation(false);

    const timer = setTimeout(() => {
      setShowCategoryAnimation(true);
    }, 40);

    return () => clearTimeout(timer);
  }, [showICD10Explorer, correctedTerm, showICD9Explorer, correctedProcedureTerm, showMedicationExplorer, normalizedMedicationTerm]);

  // Auto-scroll & animated reveal when analysis result is ready
  useEffect(() => {
    if (!result) return;

    // Reset animation state first so transition can replay on subsequent analyses
    setShowResultAnimation(false);

    const timer = setTimeout(() => {
      setShowResultAnimation(true);

      if (resultsRef.current) {
        resultsRef.current.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }
    }, 50);

    return () => clearTimeout(timer);
  }, [result]);

  // Handle Generate AI Analysis after code selection
  const handleGenerateAnalysis = async () => {
    // Auto-translate if not yet translated
    if (!correctedTerm && (diagnosis || freeText)) {
      await handleGenerate();
      return;
    }

    if (!selectedICD10Code) {
      alert('Silakan pilih kode ICD-10 terlebih dahulu');
      return;
    }
    
    setIsLoading(true);
    const startTime = Date.now();

    // ================================================
    // 1) CONSTRUCT DRUG LIST
    // ================================================
    let drugList: string[] = [];

    // ================================================
    // FIX: Gunakan nama obat generik, bukan ID sediaan
    // ================================================
    if (selectedMedicationDetails.length > 0) {
        drugList = [selectedMedicationCategory?.generic_name.toLowerCase()];
    }
    else if (medication) {
        // User ketik manual → sudah generik
        drugList = [medication.toLowerCase().split(" ")[0]];
    }

    // Jika free text → pakai hasil parsed "medication"
    else if (freeText && medication) {
      drugList = [medication];
    }
    
    try {
      // Determine input mode
      const modeToUse: InputMode = freeText.trim() ? 'text' : 'form';
      
      // Prepare request data based on input mode
      const requestData: any = modeToUse === 'text'
      ? {
          mode: 'text',
          input_text: freeText,
          drug_list: drugList,
          icd10_code: selectedICD10Code.code,
          icd9_code: selectedICD9Code?.code || null,
          use_optimized: true,
          save_history: true
        }
      : {
          mode: 'form',
          diagnosis,
          procedure,
          medication,
          service_type: serviceType,
          bpjs_class: bpjsClass,
          drug_list: drugList,
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
        const aiResult = response.data?.data ?? response.data;
        
        // Use selected ICD-10 code instead of auto-detected
        const icd10Code = selectedICD10Code.code; // Use user-selected code
        
        // Extract ICD-9 codes (support BOTH new + old format)
        const tindakanArray = aiResult.klasifikasi?.tindakan || [];

        const icd9Codes = tindakanArray
          .map((t: any) => {
            // NEW FORMAT: object { icd9: "87.09" }
            if (typeof t === 'object' && t.icd9 && t.icd9 !== '-') {
              return t.icd9;
            }

            // OLD FORMAT: "Foto thorax (87.44)"
            if (typeof t === 'string') {
              const match = t.match(/\b(\d{2}\.\d{2}|\d{2}\.\d{1}|\d{2}\d{2})\b/);
              return match ? match[1] : null;
            }

            return null;
          })
          .filter((code: any) => code);

        // Map validation status from validasi_klinis
        let validationStatus: 'valid' | 'warning' | 'invalid' = 'valid';
        const sesuaiCP = aiResult.validasi_klinis?.sesuai_cp;
        const sesuaiFornas = aiResult.validasi_klinis?.sesuai_fornas;
        
        if (sesuaiCP === false || sesuaiFornas === false) {
          validationStatus = 'invalid';
        } else if (sesuaiCP === 'parsial' || sesuaiFornas === 'parsial') {
          validationStatus = 'warning';
        }

        // Map Fornas status from fornas_validation (NEW FORMAT)
        let fornasStatus: 'sesuai' | 'tidak-sesuai' | 'perlu-review' = 'sesuai';
        const fornasValidation = aiResult.fornas_validation || {};
        const sesuaiCount = fornasValidation.sesuai_fornas || 0;
        const totalObat = fornasValidation.total_obat || 1;
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
            icd9: icd9Codes.length > 0 
                  ? icd9Codes 
                  : selectedICD9Code 
                    ? [selectedICD9Code.code] 
                    : [],
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
          // NEW: FORNAS validation data from backend
          fornasList: fornasValidation.validations || [],  // Array of {no, nama_obat, status_fornas, sumber_regulasi, updated_at, ...}
          fornasSummary: {
            total_obat: totalObat,
            sesuai: sesuaiCount,
            tidak_sesuai: fornasValidation.tidak_sesuai || 0,
            perlu_justifikasi: 0,
            update_date: fornasValidation.validations?.[0]?.updated_at || "-",
            status_database: "Active"
          },
          pnpk_summary: aiResult.pnpk_summary || null,
          aiInsight: aiResult.insight_ai || 'Analisis berhasil dilakukan.',
          consistency: {
            dx_tx: aiResult.konsistensi?.dx_tx || {},
            dx_drug: aiResult.konsistensi?.dx_drug || {},
            tx_drug: aiResult.konsistensi?.tx_drug || {},
            tingkat: aiResult.konsistensi?.tingkat_konsistensi || "-",
            score: Number(aiResult.konsistensi?._score) || 0
          },
        };

        console.log('[AdminRS] Analysis Result:', analysisResult);
        console.log('[AdminRS] FORNAS Validation:', fornasValidation);
        console.log('[AdminRS] fornasList:', analysisResult.fornasList);
        console.log('[AdminRS] PNPK Summary:', analysisResult.pnpk_summary);

        setResult(analysisResult);

        // TODO: Set INACBG result from backend when available
        // For now, set mock data untuk demo UI dengan dynamic kelas BPJS
        const selectedClass = parseInt(bpjsClass) || 1;
        const tarifByClass = {
          1: 5770100.0,
          2: 5054300.0,
          3: 4338400.0
        };
        
        const mockINACBG: INACBGResult = {
          success: true,
          cbg_code: "I-4-10-I",
          description: "INFARK MYOKARD AKUT (RINGAN)",
          tarif: tarifByClass[selectedClass as keyof typeof tarifByClass],
          tarif_detail: {
            tarif_kelas_1: 5770100.0,
            tarif_kelas_2: 5054300.0,
            tarif_kelas_3: 4338400.0,
            kelas_bpjs_used: selectedClass
          },
          breakdown: {
            cmg: "I",
            cmg_description: "Cardiovascular system",
            case_type: "4",
            case_type_description: "Rawat Inap Bukan Prosedur",
            specific_code: "10",
            severity: "I"
          },
          matching_detail: {
            strategy: "diagnosis_only_empirical",
            confidence: 80,
            case_count: 4,
            note: "40.0% kasus I21.0 masuk CBG ini"
          },
          classification: {
            regional: "1",
            kelas_rs: "B",
            tipe_rs: "Pemerintah",
            layanan: "RI"
          },
          warnings: [
            "Prosedur diabaikan, menggunakan CBG yang paling umum untuk diagnosis ini"
          ]
        };
        setInacbgResult(mockINACBG);

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
        alert(`⚠ Limit penggunaan AI harian Anda sudah habis!\n\nSilakan coba lagi besok atau hubungi admin untuk menambah limit.`);
      } else if (statusCode === 504 || errorCode === 'ECONNABORTED') {
        // Timeout error
        alert(
          `⏱ Analisis Timeout (${Math.round(processingTime / 1000)} detik)\n\n` +
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
        
        fullErrorMessage += `\n\n⏱ Processing Time: ${Math.round(processingTime / 1000)} detik`;
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

  const handleMedicationCategorySelection = (category: any) => {
    setSelectedMedicationCategory(category);
    console.log(`[FORNAS] Selected category: ${category.generic_name}`);
  };

  const handleMedicationDetailToggle = (kodeFornas: string) => {
    console.log(`[MEDICATION] Toggle kode_fornas: ${kodeFornas}`);
    console.log(`[MEDICATION] Current selected:`, selectedMedicationDetails);
    
    // SINGLE SELECTION: Replace array with single item or clear if same item clicked
    setSelectedMedicationDetails(prev => {
      if (prev.includes(kodeFornas)) {
        console.log(`[MEDICATION] Deselecting: ${kodeFornas}`);
        return []; // Clear selection
      } else {
        console.log(`[MEDICATION] Selecting (single): ${kodeFornas}`);
        return [kodeFornas]; // Replace with single selection
      }
    });
  };

  return (
    <div className="h-full flex gap-4">
      {/* Left Panel - Input (Fixed Width) */}
      <div className="w-72 flex-shrink-0">
        <div
          className={`rounded-2xl p-6 h-full ${
            isDark
              ? 'bg-slate-900/30 border border-cyan-500/25'
              : 'bg-white/40 border border-blue-100/80'
          } backdrop-blur-xl shadow-2xl flex flex-col`}
        >
          <h2
            className={`text-lg font-semibold mb-2 flex-shrink-0 ${
              isDark ? 'text-cyan-300' : 'text-blue-700'
            }`}
          >
            Smart Input Hybrid
          </h2>

          {/* AI Usage Indicator (moved to navbar profile menu) */}

          {/* Input Mode Toggle */}
          <div
            className={`flex-shrink-0 inline-flex items-center justify-center rounded-full p-1 mt-1 mb-3 border ${
              isDark
                ? 'bg-slate-900/70 border-cyan-500/30'
                : 'bg-white/80 border-blue-100 shadow-sm'
            }`}
          >
            <button
              onClick={() => handleInputModeChange('text')}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${
                inputMode === 'text'
                  ? isDark
                    ? 'bg-cyan-500 text-slate-900 shadow-md'
                    : 'bg-blue-500 text-white shadow-md'
                  : isDark
                  ? 'text-slate-300 hover:bg-slate-700/60'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <FileText className="w-3 h-3 inline mr-1.5" />
              Free Text
            </button>
            <button
              onClick={() => handleInputModeChange('form')}
              className={`ml-1 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all duration-300 ${
                inputMode === 'form'
                  ? isDark
                    ? 'bg-cyan-500 text-slate-900 shadow-md'
                    : 'bg-blue-500 text-white shadow-md'
                  : isDark
                  ? 'text-slate-300 hover:bg-slate-700/60'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <FileText className="w-3 h-3 inline mr-1.5" />
              Form Input
            </button>
          </div>

          <div className="flex-1 min-h-0">
            <SmartInputPanel
              mode={inputMode}
              diagnosis={diagnosis}
              procedure={procedure}
              medication={medication}
              serviceType={serviceType}
              bpjsClass={bpjsClass}
              freeText={freeText}
              onDiagnosisChange={handleDiagnosisChange}
              onProcedureChange={handleProcedureChange}
              onMedicationChange={handleMedicationChange}
              onServiceTypeChange={setServiceType}
              onBpjsClassChange={setBpjsClass}
              onFreeTextChange={handleFreeTextChange}
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
              ? 'bg-slate-900/30 border border-cyan-500/25'
              : 'bg-white/40 border border-blue-100/80'
          } backdrop-blur-xl shadow-2xl flex flex-col overflow-hidden`}
        >
          <h2
            className={`text-lg font-semibold mb-6 flex-shrink-0 ${
              isDark ? 'text-cyan-300' : 'text-blue-700'
            }`}
          >
            Pilih Kode Spesifik
          </h2>
          
          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto space-y-6">
            
            {/* Combined ICD Explorer Section (Diagnosis + Tindakan) */}
            {(showICD10Explorer && correctedTerm) || (showICD9Explorer && correctedProcedureTerm) ? (
              <div
                className={`flex-shrink-0 relative transform transition-all duration-500 ${
                  showCategoryAnimation ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
                }`}
              >
                {/* 2-Column Layout: Explorers (Left 65%) | Shared Mapping Preview (Right 35%) */}
                <div className="grid grid-cols-12 gap-4">
                  {/* Left Column: ICD-10 & ICD-9 Explorers (8 columns = ~66%) */}
                  <div className="col-span-8 space-y-6">
                    {/* ICD-10 Diagnosis Section */}
                    {showICD10Explorer && correctedTerm && (
                      <div>
                        <ICD10Explorer
                          searchTerm={originalSearchTerm}
                          correctedTerm={correctedTerm}
                          originalInput={{
                            diagnosis,
                            procedure,
                            medication,
                            freeText,
                            mode: freeText.trim() ? 'text' as const : 'form' as const,
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
                        <ICD9Explorer
                          searchTerm={originalProcedureTerm}
                          correctedTerm={correctedProcedureTerm}
                          synonyms={procedureSynonyms}
                          originalInput={{
                            diagnosis,
                            procedure,
                            medication,
                            freeText,
                            mode: freeText.trim() ? 'text' as const : 'form' as const,
                          }}
                          isDark={isDark}
                          isAnalyzing={isLoading}
                          onCodeSelected={handleProcedureCodeSelection}
                          hidePreview={true}
                        />
                      </div>
                    )}

                    {/* Medication FORNAS Section - ICD-like Hierarchy + AI Translation (Obat) */}
                    {showMedicationExplorer && normalizedMedicationTerm && (
                      <div className="space-y-3">
                        <div
                          className={`rounded-lg px-4 py-3 flex items-center justify-between ${
                            isDark
                              ? 'bg-emerald-500/10 border border-emerald-400/40'
                              : 'bg-emerald-50 border border-emerald-200'
                          }`}
                        >
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <Pill className={`w-4 h-4 ${isDark ? 'text-emerald-300' : 'text-emerald-600'}`} />
                              <span
                                className={`text-xs font-semibold tracking-wide uppercase ${
                                  isDark ? 'text-emerald-200' : 'text-emerald-700'
                                }`}
                              >
                                AI Translation (Obat)
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-xs md:text-sm">
                              <span className={isDark ? 'text-slate-300' : 'text-gray-600'}>
                                {originalMedicationTerm || '-'}
                              </span>
                              <span className="text-xs md:text-sm">→</span>
                              <span className={`font-semibold ${
                                isDark ? 'text-emerald-300' : 'text-emerald-700'
                              }`}>
                                {normalizedMedicationTerm}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <MedicationCategoryPanel
                            categories={medicationCategories}
                            selectedCategory={selectedMedicationCategory}
                            onSelectCategory={handleMedicationCategorySelection}
                            isLoading={isMedicationLoading}
                            isDark={isDark}
                          />
                          <MedicationDetailPanel
                            category={selectedMedicationCategory}
                            selectedDetails={selectedMedicationDetails}
                            onToggleDetail={handleMedicationDetailToggle}
                            isDark={isDark}
                          />
                        </div>
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
                      originalMedication={originalMedicationTerm}
                      selectedMedicationCategory={selectedMedicationCategory}
                      selectedMedicationDetails={selectedMedicationDetails}
                      onGenerateAnalysis={handleGenerateAnalysis}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className={`flex flex-col items-center justify-center py-20 ${
                isDark ? 'text-slate-400' : 'text-gray-500'
              }`}>
                {isLoading ? (
                  <>
                    <div
                      className={`w-10 h-10 rounded-full border-4 mb-4 animate-spin ${
                        isDark
                          ? 'border-cyan-500/30 border-t-cyan-400'
                          : 'border-blue-500/30 border-t-blue-500'
                      }`}
                    />
                    <p className="text-sm text-center px-4 mb-1">
                      AI sedang menyiapkan kategori ICD & FORNAS...
                    </p>
                    <p className="text-xs opacity-70 text-center px-4">
                      Mohon tunggu sebentar, kami mencari kode yang paling relevan.
                    </p>
                  </>
                ) : (
                  <>
                    <svg className="w-16 h-16 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="text-sm text-center px-4">
                      Klik "Generate AI Insight" untuk melihat kategori ICD yang sesuai dengan diagnosis dan tindakan
                    </p>
                  </>
                )}
              </div>
            )}

            {/* Results Section - Below Explorer */}
            {result && (
              <div
                ref={resultsRef}
                className={`flex-shrink-0 transform transition-all duration-500 ${
                  showResultAnimation ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                }`}
              >
                {/* ================== Hasil Analisis AI ================== */}
                <div
                  className={`rounded-xl p-4 mb-4 ${
                    isDark
                      ? "bg-cyan-500/10 border border-cyan-500/30"
                      : "bg-blue-50 border border-blue-200"
                  }`}
                >
                  {/* HEADER: Judul + ICD di kanan */}
                  <div className="flex items-center justify-between mb-3">

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
                      <span className={isDark ? "text-slate-600" : "text-gray-400"}>
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

                  {/* Toggle Tabs untuk Analysis vs INACBG */}
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => setResultViewMode('analysis')}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium text-sm transition-all ${
                        resultViewMode === 'analysis'
                          ? isDark
                            ? 'bg-cyan-500 text-white shadow-lg'
                            : 'bg-blue-600 text-white shadow-lg'
                          : isDark
                            ? 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      📋 Analisis Klinis
                    </button>
                    <button
                      onClick={() => setResultViewMode('inacbg')}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium text-sm transition-all ${
                        resultViewMode === 'inacbg'
                          ? isDark
                            ? 'bg-cyan-500 text-white shadow-lg'
                            : 'bg-blue-600 text-white shadow-lg'
                          : isDark
                            ? 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      💰 INA-CBG
                    </button>
                  </div>
                </div>

                {/* Conditional Panel based on resultViewMode */}
                {resultViewMode === 'analysis' ? (
                  <ResultsPanel result={result} isDark={isDark} />
                ) : (
                  <INACBGPanel result={inacbgResult} isDark={isDark} />
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      {/* End Right Panel */}
    </div>
  );
}