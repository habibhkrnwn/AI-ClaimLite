/**
 * ICD-10 Common Terms Mapping
 * Maps medical ICD-10 codes to common Indonesian terms
 */

interface CommonTermMapping {
  [key: string]: string;
}

// HEAD codes common terms
export const headCodeCommonTerms: CommonTermMapping = {
  // Pneumonia codes
  'J12': 'Radang Paru-paru karena Virus',
  'J13': 'Radang Paru-paru karena Bakteri Pneumokokus',
  'J14': 'Radang Paru-paru karena Bakteri Haemophilus',
  'J15': 'Radang Paru-paru karena Bakteri',
  'J16': 'Radang Paru-paru karena Mikroorganisme Lain',
  'J17': 'Radang Paru-paru akibat Penyakit Bakteri Lain',
  'J18': 'Radang Paru-paru (Tidak Spesifik)',
  
  // Upper respiratory infections
  'J00': 'Pilek Biasa',
  'J01': 'Sinusitis Akut',
  'J02': 'Radang Tenggorokan Akut',
  'J03': 'Radang Amandel Akut',
  'J04': 'Radang Laring dan Trakea',
  'J05': 'Radang Laring Obstruktif Akut (Croup)',
  'J06': 'Infeksi Saluran Napas Atas Akut',
  
  // Lower respiratory infections
  'J20': 'Bronkitis Akut',
  'J21': 'Bronkiolitis Akut',
  'J22': 'Infeksi Saluran Napas Bawah Akut',
  
  // Chronic respiratory diseases
  'J40': 'Bronkitis (Tidak Spesifik)',
  'J41': 'Bronkitis Kronis Sederhana dan Mukopurulen',
  'J42': 'Bronkitis Kronis (Tidak Spesifik)',
  'J43': 'Emfisema',
  'J44': 'Penyakit Paru Obstruktif Kronis (PPOK)',
  'J45': 'Asma',
  'J46': 'Serangan Asma Berat',
  
  // Tuberculosis
  'A15': 'TB Paru dengan Pemeriksaan Positif',
  'A16': 'TB Paru tanpa Pemeriksaan',
  'A17': 'TB Sistem Saraf',
  'A18': 'TB Organ Lain',
  'A19': 'TB Miliaria (Tersebar)',
  
  // Typhoid
  'A01': 'Tifoid dan Paratifoid',
  
  // Diarrhea
  'A09': 'Diare dan Gastroenteritis',
  
  // Dengue
  'A90': 'Demam Berdarah Dengue (DBD)',
  'A91': 'Demam Dengue Berat',
  
  // Diabetes
  'E10': 'Diabetes Tipe 1',
  'E11': 'Diabetes Tipe 2',
  'E12': 'Diabetes terkait Malnutrisi',
  'E13': 'Diabetes Tipe Lain',
  'E14': 'Diabetes (Tidak Spesifik)',
  
  // Hypertension
  'I10': 'Tekanan Darah Tinggi',
  'I11': 'Penyakit Jantung Hipertensi',
  'I12': 'Penyakit Ginjal Hipertensi',
  'I13': 'Penyakit Jantung dan Ginjal Hipertensi',
  
  // Heart diseases
  'I20': 'Angina Pektoris (Nyeri Dada)',
  'I21': 'Serangan Jantung Akut',
  'I25': 'Penyakit Jantung Koroner Kronis',
  
  // Stroke
  'I60': 'Pendarahan Otak (Subarachnoid)',
  'I61': 'Pendarahan Otak',
  'I63': 'Stroke Iskemik',
  'I64': 'Stroke (Tidak Spesifik)',
  
  // Injuries
  'S00': 'Luka Kepala Superfisial',
  'S01': 'Luka Terbuka di Kepala',
  'S06': 'Cedera Otak',
  'S50': 'Luka Siku dan Lengan Bawah',
  'S60': 'Luka Pergelangan Tangan dan Tangan',
  'S80': 'Luka Kaki Bagian Bawah',
  'S90': 'Luka Pergelangan Kaki dan Kaki',
  
  // Fractures
  'S42': 'Patah Tulang Bahu dan Lengan Atas',
  'S52': 'Patah Tulang Lengan Bawah',
  'S62': 'Patah Tulang Pergelangan Tangan dan Tangan',
  'S72': 'Patah Tulang Paha',
  'S82': 'Patah Tulang Kaki Bawah',
  
  // Pregnancy complications
  'O00': 'Kehamilan Ektopik',
  'O20': 'Pendarahan pada Kehamilan Muda',
  'O80': 'Persalinan Normal',
  
  // Allergies
  'T78': 'Reaksi Alergi',
  'T88': 'Komplikasi Medis dan Bedah',
  
  // Drug reactions
  'Y57': 'Efek Samping Obat',
  'Z88': 'Riwayat Alergi Obat',
  
  // Chickenpox
  'B01': 'Cacar Air',
  
  // Measles
  'B05': 'Campak',
  
  // Hepatitis
  'B15': 'Hepatitis A',
  'B16': 'Hepatitis B',
  'B17': 'Hepatitis Virus Akut Lainnya',
  'B18': 'Hepatitis Virus Kronis',
  'B19': 'Hepatitis Virus (Tidak Spesifik)',
  
  // COVID-19
  'U07': 'COVID-19',
  
  // Malaria
  'B50': 'Malaria Plasmodium Falciparum',
  'B51': 'Malaria Plasmodium Vivax',
  'B52': 'Malaria Plasmodium Malariae',
  'B53': 'Malaria Jenis Lain',
  'B54': 'Malaria (Tidak Spesifik)',
};

// Sub-codes common terms
export const subCodeCommonTerms: CommonTermMapping = {
  // J12 - Viral pneumonia
  'J12.0': 'Radang Paru karena Virus Adenovirus',
  'J12.1': 'Radang Paru karena Virus RSV',
  'J12.2': 'Radang Paru karena Virus Parainfluenza',
  'J12.3': 'Radang Paru karena Human Metapneumovirus',
  'J12.8': 'Radang Paru karena Virus Lainnya',
  'J12.9': 'Radang Paru karena Virus (Tidak Spesifik)',
  
  // J15 - Bacterial pneumonia
  'J15.0': 'Radang Paru karena Bakteri Klebsiella',
  'J15.1': 'Radang Paru karena Bakteri Pseudomonas',
  'J15.2': 'Radang Paru karena Bakteri Stafilokokus',
  'J15.3': 'Radang Paru karena Bakteri Streptokokus Grup B',
  'J15.4': 'Radang Paru karena Bakteri Streptokokus Lain',
  'J15.5': 'Radang Paru karena Bakteri E. Coli',
  'J15.6': 'Radang Paru karena Bakteri Gram-negatif',
  'J15.7': 'Radang Paru karena Mikoplasma',
  'J15.8': 'Radang Paru karena Bakteri Lainnya',
  'J15.9': 'Radang Paru karena Bakteri (Tidak Spesifik)',
  
  // J18 - Pneumonia, unspecified
  'J18.0': 'Radang Paru karena Bronkopneumonia',
  'J18.1': 'Radang Paru Lobaris (Tidak Spesifik)',
  'J18.2': 'Radang Paru Hipostatik',
  'J18.8': 'Radang Paru Lainnya',
  'J18.9': 'Radang Paru (Tidak Spesifik)',
  
  // B01 - Varicella (Chickenpox)
  'B01.0': 'Cacar Air dengan Meningitis',
  'B01.1': 'Cacar Air dengan Radang Otak',
  'B01.2': 'Cacar Air dengan Radang Paru',
  'B01.8': 'Cacar Air dengan Komplikasi Lain',
  'B01.9': 'Cacar Air tanpa Komplikasi',
  
  // E11 - Type 2 diabetes
  'E11.0': 'Diabetes Tipe 2 dengan Koma',
  'E11.1': 'Diabetes Tipe 2 dengan Ketoasidosis',
  'E11.2': 'Diabetes Tipe 2 dengan Gangguan Ginjal',
  'E11.3': 'Diabetes Tipe 2 dengan Gangguan Mata',
  'E11.4': 'Diabetes Tipe 2 dengan Gangguan Saraf',
  'E11.5': 'Diabetes Tipe 2 dengan Gangguan Pembuluh Darah',
  'E11.6': 'Diabetes Tipe 2 dengan Komplikasi Lain',
  'E11.7': 'Diabetes Tipe 2 dengan Komplikasi Ganda',
  'E11.8': 'Diabetes Tipe 2 dengan Komplikasi Tidak Spesifik',
  'E11.9': 'Diabetes Tipe 2 tanpa Komplikasi',
  
  // A09 - Diarrhea
  'A09.0': 'Diare Infeksi',
  'A09.9': 'Diare (Tidak Spesifik)',
  
  // I10 - Hypertension (usually no subcodes, but some systems have)
  'I10.0': 'Hipertensi Esensial Jinak',
  'I10.1': 'Hipertensi Esensial Ganas',
  'I10.9': 'Hipertensi Esensial (Tidak Spesifik)',
};

/**
 * Get common term for ICD-10 code
 */
export function getCommonTerm(code: string): string | null {
  // Try exact match first
  if (subCodeCommonTerms[code]) {
    return subCodeCommonTerms[code];
  }
  
  if (headCodeCommonTerms[code]) {
    return headCodeCommonTerms[code];
  }
  
  // Try HEAD code match (first 3 characters)
  const headCode = code.substring(0, 3);
  if (headCodeCommonTerms[headCode]) {
    return headCodeCommonTerms[headCode];
  }
  
  return null;
}

/**
 * Check if code has common term
 */
export function hasCommonTerm(code: string): boolean {
  return getCommonTerm(code) !== null;
}
