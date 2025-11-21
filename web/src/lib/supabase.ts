import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface Analysis {
  id: string;
  diagnosis: string;
  procedure: string;
  medication: string;
  result: AnalysisResult;
  created_at: string;
}

export interface INACBGResult {
  success: boolean;
  cbg_code: string;
  description: string;
  tarif: number;
  tarif_detail: {
    tarif_kelas_1: number;
    tarif_kelas_2: number;
    tarif_kelas_3: number;
    kelas_bpjs_used: number;
  };
  breakdown: {
    cmg: string;
    cmg_description: string;
    case_type: string;
    case_type_description: string;
    specific_code: string;
    severity: string;
  };
  matching_detail: {
    strategy: string;
    confidence: number;
    case_count: number;
    note: string;
  };
  classification: {
    regional: string;
    kelas_rs: string;
    tipe_rs: string;
    layanan: string;
  };
  warnings?: string[];
}

export interface DiagnosisItem {
  name: string;
  icd10: string | null;
}

export interface AnalysisResult {
  classification: {
    icd10: string[];
    icd9: string[];
    diagnosis_primer?: DiagnosisItem;  // NEW: Primary diagnosis
    diagnosis_sekunder?: DiagnosisItem[];  // NEW: Secondary diagnoses
  };
  validation: {
    status: 'valid' | 'warning' | 'invalid';
    message: string;
  };
  // severity: 'ringan' | 'sedang' | 'berat';
  cpNasional: { tahap: string; keterangan: string }[];
  requiredDocs: string[];
  fornas: {
    status: 'sesuai' | 'tidak-sesuai' | 'perlu-review';
    message: string;
  };
  fornasList: any[];        // ADD
  fornasSummary: any;
  aiInsight: string;
  consistency: {
    dx_tx: {
      status: string;
      catatan: string;
    };
    dx_drug: {
      status: string;
      catatan: string;
    };
    tx_drug: {
      status: string;
      catatan: string;
    };
    tingkat: string;   // "Rendah" | "Sedang" | "Tinggi"
    score: number;     // tetap ada BIAR PARSING TIDAK ERROR (abaikan di UI)
  };
  inacbg?: INACBGResult;  // Optional INACBG result
}
