import { AnalysisResult } from './supabase';

export async function generateAIAnalysis(
  // diagnosis: string,
  // procedure: string,
  // medication: string
): Promise<AnalysisResult> {
  await new Promise(resolve => setTimeout(resolve, 2000));

  // const severityOptions: Array<'ringan' | 'sedang' | 'berat'> = ['ringan', 'sedang', 'berat'];
  // const randomSeverity = severityOptions[Math.floor(Math.random() * severityOptions.length)];

  const consistency = Math.floor(Math.random() * 100);

  return {
    classification: {
      icd10: ['A09', 'K52.9', 'E86.0'],
      icd9: ['45.13', '96.6', '87.63'],
    },
    validation: {
      status: consistency > 80 ? 'valid' : consistency > 60 ? 'warning' : 'invalid',
      message: consistency > 80
        ? 'Diagnosis, tindakan, dan obat sudah konsisten'
        : 'Perlu review kesesuaian diagnosis dengan tindakan',
    },
    // severity: randomSeverity,
    cpNasional: [
      { tahap: "Tahap Awal", keterangan: " CP Nasional dari mock AI" }
    ],
    requiredDocs: ['Resume Medis', 'Hasil Laboratorium', 'Resep Obat', 'Informed Consent'],
    fornas: {
      status: Math.random() > 0.3 ? 'sesuai' : 'perlu-review',
      message: Math.random() > 0.3
        ? 'Obat yang diresepkan sesuai dengan Formularium Nasional'
        : 'Beberapa obat perlu review kesesuaian dengan indikasi',
    },
    fornasList: [
      { nama: 'Paracetamol', keterangan: ' obat dari mock AI' },
      { nama: 'Ibuprofen', keterangan: ' obat dari mock AI' },
      { nama: 'Aspirin', keterangan: ' obat dari mock AI' }
    ],
    fornasSummary: {
      total: 3,
      sesuai: 2,
      perluReview: 1
    },
    aiInsight: 'Pastikan dokumentasi hasil laboratorium dilampirkan. Pertimbangkan pemeriksaan elektrolit untuk pasien dengan dehidrasi sedang-berat.',
    consistency: {
      dx_tx: {
        status: "⚠ Parsial",
        catatan: "diagnosis dan tindakan sebagian sesuai"
      },
      dx_drug: {
        status: "❌ Tidak Sesuai",
        catatan: "obat tidak match diagnosis"
      },
      tx_drug: {
        status: "⚠ Parsial",
        catatan: "obat sebagian match tindakan"
      },
      tingkat: "sedang",
      score: 75
    }
  };
}
