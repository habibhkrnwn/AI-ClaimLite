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

export interface AnalysisResult {
  classification: {
    icd10: string[];
    icd9: string[];
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
  pnpk_summary?: any;       // ADD for PNPK compliance
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
}
