import { useState } from 'react';
import INACBGPanel from './INACBGPanel';
import { Moon, Sun } from 'lucide-react';

// Mock data sesuai dengan JSON yang diberikan
const mockINACBGResult = {
  success: true,
  cbg_code: "I-4-10-I",
  description: "INFARK MYOKARD AKUT (RINGAN)",
  tarif: 5770100.0,
  tarif_detail: {
    tarif_kelas_1: 5770100.0,
    tarif_kelas_2: 5054300.0,
    tarif_kelas_3: 4338400.0,
    kelas_bpjs_used: 1
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

export default function INACBGDemo() {
  const [isDark, setIsDark] = useState(true);
  const [showResult, setShowResult] = useState(true);

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDark 
        ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900' 
        : 'bg-gradient-to-br from-blue-50 via-white to-cyan-50'
    }`}>
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold mb-2 ${
              isDark ? 'text-cyan-300' : 'text-blue-700'
            }`}>
              📊 INA-CBG Analyzer - Demo UI
            </h1>
            <p className={`text-sm ${
              isDark ? 'text-slate-400' : 'text-gray-600'
            }`}>
              Preview tampilan hasil analisis INA-CBG (Backend belum tersedia)
            </p>
          </div>
          
          {/* Theme Toggle */}
          <button
            onClick={() => setIsDark(!isDark)}
            className={`p-3 rounded-lg transition-all duration-300 ${
              isDark
                ? 'bg-slate-700 hover:bg-slate-600 text-yellow-400'
                : 'bg-blue-100 hover:bg-blue-200 text-blue-700'
            }`}
          >
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>

        {/* Control Panel */}
        <div className={`rounded-xl p-4 mb-6 ${
          isDark
            ? 'bg-slate-800/60 border border-cyan-500/20'
            : 'bg-white/80 border border-blue-200'
        } backdrop-blur-md shadow-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className={`font-semibold mb-1 ${
                isDark ? 'text-cyan-300' : 'text-blue-700'
              }`}>
                Mode Preview
              </h3>
              <p className={`text-xs ${
                isDark ? 'text-slate-400' : 'text-gray-600'
              }`}>
                Toggle untuk melihat state kosong vs. dengan data
              </p>
            </div>
            <button
              onClick={() => setShowResult(!showResult)}
              className={`px-6 py-2 rounded-lg font-medium transition-all duration-300 ${
                showResult
                  ? isDark
                    ? 'bg-cyan-500 hover:bg-cyan-600 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                  : isDark
                    ? 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              }`}
            >
              {showResult ? 'Tampilkan Data' : 'Sembunyikan Data'}
            </button>
          </div>
        </div>

        {/* INACBG Panel */}
        <div className={`rounded-xl p-6 ${
          isDark
            ? 'bg-slate-800/40 border border-cyan-500/20'
            : 'bg-white/60 border border-blue-100'
        } backdrop-blur-xl shadow-2xl`}>
          <div className="flex items-center gap-2 mb-4">
            <div className={`w-2 h-8 rounded-full ${
              isDark ? 'bg-cyan-400' : 'bg-blue-500'
            }`} />
            <h2 className={`text-xl font-bold ${
              isDark ? 'text-cyan-300' : 'text-blue-700'
            }`}>
              Hasil Analisis INACBG
            </h2>
          </div>

          <div className="h-[calc(100vh-300px)]">
            <INACBGPanel 
              result={showResult ? mockINACBGResult : null} 
              isDark={isDark} 
            />
          </div>
        </div>

        {/* Footer Info */}
        <div className={`mt-6 p-4 rounded-lg text-center text-sm ${
          isDark
            ? 'bg-slate-800/40 text-slate-400 border border-slate-700'
            : 'bg-white/60 text-gray-600 border border-gray-200'
        }`}>
          💡 <strong>Note:</strong> Ini adalah UI preview. Backend service INA-CBG akan diintegrasikan setelah pull dari repository.
        </div>
      </div>
    </div>
  );
}
