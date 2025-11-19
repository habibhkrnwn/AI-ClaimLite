import { DollarSign, AlertCircle, CheckCircle, Info, TrendingUp } from 'lucide-react';

interface INACBGResult {
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

interface INACBGPanelProps {
  result: INACBGResult | null;
  isDark: boolean;
}

export default function INACBGPanel({ result, isDark }: INACBGPanelProps) {
  if (!result) {
    return (
      <div className={`flex items-center justify-center h-full ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>
        <div className="text-center space-y-3">
          <DollarSign className="w-16 h-16 mx-auto opacity-30" />
          <p className="text-sm">Hasil analisis INA-CBG akan muncul di sini</p>
        </div>
      </div>
    );
  }

  const formatRupiah = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const cardClass = `rounded-xl p-5 ${
    isDark
      ? 'bg-slate-800/40 border border-cyan-500/20'
      : 'bg-white/60 border border-blue-100'
  } backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-300`;

  return (
    <div className="space-y-4 overflow-y-auto max-h-full pr-2">
      
      {/* ==================== CBG CODE & DESCRIPTION ====================== */}
      <div className={cardClass}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
              <h3 className={`text-lg font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                Kode CBG
              </h3>
            </div>
            <div className="mt-3">
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-2xl font-bold ${
                isDark ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'bg-blue-100 text-blue-700 border border-blue-200'
              }`}>
                {result.cbg_code}
              </div>
              <p className={`mt-3 text-base font-medium ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {result.description}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ==================== TARIF SECTION ====================== */}
      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`text-lg font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            Tarif INA-CBG
          </h3>
        </div>

        {/* Main Tarif */}
        <div className={`mb-4 p-4 rounded-lg ${
          isDark ? 'bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30' : 'bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200'
        }`}>
          <div className="text-center">
            <div className={`text-sm font-medium mb-1 ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>
              Tarif Kelas {result.tarif_detail.kelas_bpjs_used}
            </div>
            <div className={`text-3xl font-bold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              {formatRupiah(result.tarif)}
            </div>
          </div>
        </div>

        {/* Tarif Detail by Class */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { kelas: 1, tarif: result.tarif_detail.tarif_kelas_1 },
            { kelas: 2, tarif: result.tarif_detail.tarif_kelas_2 },
            { kelas: 3, tarif: result.tarif_detail.tarif_kelas_3 },
          ].map(({ kelas, tarif }) => {
            const isActive = kelas === result.tarif_detail.kelas_bpjs_used;
            return (
              <div
                key={kelas}
                className={`p-3 rounded-lg border text-center ${
                  isActive
                    ? isDark
                      ? 'bg-cyan-500/20 border-cyan-500/50'
                      : 'bg-blue-100 border-blue-300'
                    : isDark
                    ? 'bg-slate-700/30 border-slate-600/30'
                    : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className={`text-xs font-medium mb-1 ${
                  isDark ? 'text-slate-400' : 'text-gray-600'
                }`}>
                  Kelas {kelas}
                </div>
                <div className={`text-sm font-bold ${
                  isActive
                    ? isDark ? 'text-cyan-300' : 'text-blue-700'
                    : isDark ? 'text-slate-300' : 'text-gray-700'
                }`}>
                  {formatRupiah(tarif)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ==================== BREAKDOWN & CLASSIFICATION ====================== */}
      <div className="grid grid-cols-2 gap-4">
        
        {/* Breakdown */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              Breakdown CBG
            </h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className={`flex justify-between items-center py-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>CMG</span>
              <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {result.breakdown.cmg}
              </span>
            </div>
            <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'} pl-2 pb-2`}>
              {result.breakdown.cmg_description}
            </div>
            <div className={`flex justify-between items-center py-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Case Type</span>
              <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {result.breakdown.case_type}
              </span>
            </div>
            <div className={`text-xs ${isDark ? 'text-slate-500' : 'text-gray-500'} pl-2 pb-2`}>
              {result.breakdown.case_type_description}
            </div>
            <div className={`flex justify-between items-center py-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Specific Code</span>
              <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {result.breakdown.specific_code}
              </span>
            </div>
            <div className={`flex justify-between items-center py-2 ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Severity</span>
              <span className={`font-bold text-3xl font-serif ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
                {result.breakdown.severity}
              </span>
            </div>
          </div>
        </div>

        {/* Classification */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <Info className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              Klasifikasi
            </h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className={`flex justify-between items-center py-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Regional</span>
              <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {result.classification.regional}
              </span>
            </div>
            <div className={`flex justify-between items-center py-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Kelas RS</span>
              <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {result.classification.kelas_rs}
              </span>
            </div>
            <div className={`flex justify-between items-center py-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Tipe RS</span>
              <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {result.classification.tipe_rs}
              </span>
            </div>
            <div className={`flex justify-between items-center py-2 ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Layanan</span>
              <span className={`font-medium ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                {result.classification.layanan}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ==================== WARNINGS ====================== */}
      {result.warnings && result.warnings.length > 0 && (
        <div className={`rounded-xl p-5 ${
          isDark
            ? 'bg-yellow-500/10 border border-yellow-500/30'
            : 'bg-yellow-50 border border-yellow-200'
        } backdrop-blur-md shadow-lg`}>
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className={`w-5 h-5 ${isDark ? 'text-yellow-400' : 'text-yellow-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-yellow-300' : 'text-yellow-700'}`}>
              Peringatan
            </h3>
          </div>
          <ul className="space-y-2">
            {result.warnings.map((warning, idx) => (
              <li
                key={idx}
                className={`flex items-start gap-2 text-sm ${
                  isDark ? 'text-yellow-200' : 'text-yellow-800'
                }`}
              >
                <span className="mt-1">⚠️</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
