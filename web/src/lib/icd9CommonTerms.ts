/**
 * ICD-9 Common Terms Mapping
 * Maps medical ICD-9 procedure codes to common Indonesian terms
 */

interface CommonTermMapping {
  [key: string]: string;
}

// HEAD codes common terms (ICD-9 Procedures)
export const icd9HeadCodeCommonTerms: CommonTermMapping = {
  // Diagnostic procedures
  '87': 'Pemeriksaan Radiologi',
  '87.0': 'Rontgen Tengkorak',
  '87.1': 'Rontgen Tulang Belakang',
  '87.2': 'Rontgen Tulang Lainnya',
  '87.3': 'Rontgen Jaringan Lunak',
  '87.4': 'Foto Dada (Thorax)',
  '87.5': 'Rontgen Perut (Abdomen)',
  '87.6': 'Rontgen Panggul dan Pinggul',
  '87.7': 'Mammografi',
  
  '88': 'Pemeriksaan Radiologi Lanjutan',
  '88.0': 'CT Scan',
  '88.1': 'CT Scan Kepala',
  '88.2': 'Arteriografi (Foto Pembuluh Darah)',
  '88.3': 'Pencitraan Jantung',
  '88.4': 'Arteriografi Organ Lain',
  '88.5': 'Angiokardiografi (Foto Jantung)',
  '88.6': 'Phlebografi (Foto Vena)',
  '88.7': 'USG (Ultrasonografi)',
  '88.9': 'MRI dan Pemeriksaan Lainnya',
  
  // Endoscopy
  '45': 'Endoskopi Saluran Cerna',
  '45.1': 'Endoskopi Usus Halus',
  '45.2': 'Kolonoskopi',
  '45.3': 'Biopsi Usus',
  
  '42': 'Endoskopi Lambung dan Kerongkongan',
  '42.2': 'Endoskopi Lambung (Gastroskopi)',
  
  // Cardiovascular procedures
  '36': 'Prosedur Jantung dan Pembuluh Darah',
  '36.0': 'Pembuangan Cairan dari Jantung',
  '36.1': 'Operasi Bypass Jantung',
  '36.2': 'Revaskularisasi Jantung',
  
  '37': 'Prosedur Jantung Lainnya',
  '37.2': 'Kateterisasi Jantung',
  '37.5': 'Penggantian Katup Jantung',
  '37.7': 'Pemasangan Alat Pacu Jantung',
  '37.8': 'Pemasangan Defibrilator',
  
  // Respiratory procedures
  '33': 'Prosedur Paru-paru dan Bronkus',
  '33.2': 'Bronkoskopi',
  '33.3': 'Pembersihan Bronkus',
  
  '34': 'Operasi Dada',
  '34.0': 'Drainase Dada',
  '34.2': 'Biopsi Paru',
  
  '96': 'Terapi Non-Operatif',
  '96.0': 'Intubasi dan Ventilasi',
  '96.3': 'Nebulisasi',
  '96.4': 'Terapi Oksigen',
  '96.5': 'Cuci Darah (Hemodialisis)',
  '96.7': 'Cuci Darah Peritoneal',
  
  // Obstetric procedures
  '73': 'Prosedur Persalinan Buatan',
  '73.0': 'Induksi Persalinan Buatan',
  '73.5': 'Vakum Ekstraksi',
  '73.6': 'Forceps',
  
  '74': 'Operasi Caesar',
  '74.0': 'Operasi Caesar Klasik',
  '74.1': 'Operasi Caesar Segmen Bawah',
  
  // Surgical procedures
  '38': 'Operasi Pembuluh Darah',
  '38.0': 'Pengikatan Pembuluh Darah',
  '38.1': 'Endarterektomi',
  
  '39': 'Prosedur Vaskular Lainnya',
  '39.1': 'Transfusi Darah',
  '39.2': 'Transplantasi Pembuluh Darah',
  
  '40': 'Operasi Kelenjar Getah Bening',
  '40.2': 'Biopsi Kelenjar Getah Bening',
  '40.3': 'Pengangkatan Kelenjar Getah Bening',
  
  '47': 'Operasi Usus Buntu',
  '47.0': 'Appendektomi (Pengangkatan Usus Buntu)',
  
  '51': 'Operasi Kantung Empedu',
  '51.2': 'Kolesistektomi (Pengangkatan Kantung Empedu)',
  
  '53': 'Operasi Hernia',
  '53.0': 'Perbaikan Hernia Unilateral',
  '53.1': 'Perbaikan Hernia Bilateral',
  
  '54': 'Operasi Perut',
  '54.1': 'Laparotomi Eksplorasi',
  '54.2': 'Biopsi Peritoneum',
  
  '68': 'Operasi Rahim',
  '68.4': 'Histerektomi Abdominal (Pengangkatan Rahim)',
  '68.5': 'Histerektomi Vaginal',
  
  '69': 'Prosedur Rahim Lainnya',
  '69.0': 'Kuretase (Kerokan)',
  
  // Laboratory procedures
  '90': 'Tes Laboratorium',
  '90.0': 'Tes Darah Lengkap',
  '90.5': 'Tes Urin',
  
  '91': 'Tes Fungsi Organ',
  '91.5': 'Tes Fungsi Hati',
  
  '92': 'Tes Jantung',
  '92.0': 'EKG (Elektrokardiogram)',
  '92.1': 'Elektrokardiogram Ambulatori',
  
  '93': 'Terapi Fisik dan Rehabilitasi',
  '93.0': 'Terapi Fisik',
  '93.1': 'Terapi Okupasi',
  '93.3': 'Terapi Pernapasan',
  
  '94': 'Terapi Psikiatri',
  '94.0': 'Psikoterapi',
  
  '99': 'Prosedur Non-Operatif Lainnya',
  '99.0': 'Perawatan Luka',
  '99.2': 'Injeksi dan Infus',
  '99.6': 'Konversi Irama Jantung',
};

// Sub-codes common terms
export const icd9SubCodeCommonTerms: CommonTermMapping = {
  // Ultrasound procedures
  '88.71': 'USG Kepala dan Leher',
  '88.72': 'USG Jantung (Ekokardiografi)',
  '88.73': 'USG Dada',
  '88.74': 'USG Perut (Abdomen)',
  '88.75': 'USG Panggul',
  '88.76': 'USG Kepala (Bayi)',
  '88.77': 'USG Pembuluh Darah Perifer',
  '88.78': 'USG Kandungan (Kehamilan)',
  '88.79': 'USG Bagian Tubuh Lainnya',
  
  // CT Scan
  '88.01': 'CT Scan Kepala',
  '88.02': 'CT Scan Dada (Thorax)',
  '88.38': 'CT Scan Jantung',
  
  // MRI
  '88.91': 'MRI Otak dan Batang Otak',
  '88.92': 'MRI Dada dan Tulang Rusuk',
  '88.93': 'MRI Tulang Belakang',
  '88.94': 'MRI Tulang dan Sendi',
  '88.95': 'MRI Panggul, Prostat, dan Kandung Kemih',
  '88.97': 'MRI Pembuluh Darah',
  
  // X-Ray procedures
  '87.03': 'Rontgen Gigi',
  '87.41': 'Foto Thorax (Rontgen Dada)',
  '87.44': 'Foto Thorax PA dan Lateral',
  '87.49': 'Foto Thorax Lainnya',
  
  // Cardiac procedures
  '37.21': 'Kateterisasi Jantung Kanan',
  '37.22': 'Kateterisasi Jantung Kiri',
  '37.23': 'Kateterisasi Jantung Kanan dan Kiri',
  '37.51': 'Penggantian Katup Aorta',
  '37.52': 'Penggantian Katup Mitral',
  '37.70': 'Pemasangan Alat Pacu Jantung Permanen',
  '37.72': 'Pemasangan Alat Pacu Jantung Sementara',
  
  // Blood transfusion
  '99.03': 'Transfusi Whole Blood',
  '99.04': 'Transfusi PRC (Packed Red Cells)',
  '99.05': 'Transfusi Trombosit',
  '99.06': 'Transfusi Faktor Pembekuan',
  '99.07': 'Transfusi Plasma',
  
  // Dialysis
  '39.95': 'Cuci Darah (Hemodialisis)',
  '54.98': 'Cuci Darah Peritoneal (CAPD)',
  
  // Respiratory support
  '96.04': 'Intubasi Endotrakeal',
  '96.05': 'Ventilator (Alat Bantu Napas) Lainnya',
  '96.70': 'Ventilasi Mekanik Kontinyu',
  '96.71': 'Ventilasi Mekanik Intermiten',
  '96.72': 'Ventilasi Mekanik Kurang dari 96 Jam',
  
  // Injection procedures
  '99.21': 'Injeksi Antibiotik',
  '99.22': 'Injeksi Obat Lainnya',
  '99.25': 'Injeksi Kortikosteroid',
  '99.29': 'Injeksi Obat Terapeutik Lainnya',
  
  // Surgery procedures
  '47.09': 'Appendektomi Laparoskopi',
  '47.01': 'Appendektomi dengan Drainase Abses',
  '51.22': 'Kolesistektomi Laparoskopi',
  '51.23': 'Kolesistektomi Laparoskopi dengan ERCP',
  
  // Obstetric procedures
  '73.01': 'Induksi Persalinan dengan Oksitosin',
  '73.09': 'Induksi Persalinan Lainnya',
  '73.59': 'Vakum Ekstraksi Lainnya',
  '74.0': 'Operasi Caesar Klasik',
  '74.1': 'Operasi Caesar Segmen Bawah',
  '74.2': 'Operasi Caesar Ekstraperitoneal',
  
  // Wound care
  '99.01': 'Perawatan Luka Minor',
  '99.02': 'Perawatan Luka Mayor',
};

/**
 * Get common term for ICD-9 code
 */
export function getICD9CommonTerm(code: string): string | null {
  // Try exact match first
  if (icd9SubCodeCommonTerms[code]) {
    return icd9SubCodeCommonTerms[code];
  }
  
  if (icd9HeadCodeCommonTerms[code]) {
    return icd9HeadCodeCommonTerms[code];
  }
  
  // Try HEAD code match (first 2-3 digits before decimal)
  if (code.includes('.')) {
    const parts = code.split('.');
    const headCode = `${parts[0]}.${parts[1][0]}`;
    if (icd9HeadCodeCommonTerms[headCode]) {
      return icd9HeadCodeCommonTerms[headCode];
    }
  }
  
  // Try main code (before decimal)
  const mainCode = code.split('.')[0];
  if (icd9HeadCodeCommonTerms[mainCode]) {
    return icd9HeadCodeCommonTerms[mainCode];
  }
  
  return null;
}

/**
 * Check if ICD-9 code has common term
 */
export function hasICD9CommonTerm(code: string): boolean {
  return getICD9CommonTerm(code) !== null;
}
