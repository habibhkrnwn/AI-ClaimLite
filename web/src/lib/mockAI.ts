import { AnalysisResult } from './supabase';

export async function generateAIAnalysis(
  diagnosis: string,
  procedure: string,
  medication: string
): Promise<AnalysisResult> {
  await new Promise(resolve => setTimeout(resolve, 2000));

  const severityOptions: Array<'ringan' | 'sedang' | 'berat'> = ['ringan', 'sedang', 'berat'];
  const randomSeverity = severityOptions[Math.floor(Math.random() * severityOptions.length)];

  const consistency = Math.floor(Math.random() * 30) + 70;

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
    severity: randomSeverity,
    cpNasional: 'Pasien dengan gastroenteritis akut memerlukan rehidrasi cairan, monitoring elektrolit, dan antibiotik bila diperlukan berdasarkan kultur.',
    requiredDocs: ['Resume Medis', 'Hasil Laboratorium', 'Resep Obat', 'Informed Consent'],
    fornas: {
      status: Math.random() > 0.3 ? 'sesuai' : 'perlu-review',
      message: Math.random() > 0.3
        ? 'Obat yang diresepkan sesuai dengan Formularium Nasional'
        : 'Beberapa obat perlu review kesesuaian dengan indikasi',
    },
    aiInsight: 'Pastikan dokumentasi hasil laboratorium dilampirkan. Pertimbangkan pemeriksaan elektrolit untuk pasien dengan dehidrasi sedang-berat.',
    consistency: consistency,
  };
}
