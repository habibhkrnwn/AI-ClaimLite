import { FileText, Activity, Pill } from 'lucide-react';

type InputMode = 'form' | 'text';

interface InputPanelProps {
  mode: InputMode;
  diagnosis: string;
  procedure: string;
  medication: string;
  freeText: string;
  onDiagnosisChange: (value: string) => void;
  onProcedureChange: (value: string) => void;
  onMedicationChange: (value: string) => void;
  onFreeTextChange: (value: string) => void;
  onGenerate: () => void;
  isLoading: boolean;
  isDark: boolean;
  aiUsage?: { used: number; remaining: number; limit: number } | null;
}

export default function InputPanel({
  mode,
  diagnosis,
  procedure,
  medication,
  freeText,
  onDiagnosisChange,
  onProcedureChange,
  onMedicationChange,
  onFreeTextChange,
  onGenerate,
  isLoading,
  isDark,
  aiUsage,
}: InputPanelProps) {
  // Check if AI limit is reached
  const isLimitReached = aiUsage ? aiUsage.remaining === 0 : false;

  // Mode: text - Free text input
  if (mode === 'text') {
    return (
      <div className="flex flex-col h-full gap-3">
        <div className="flex-1 flex flex-col min-h-0">
          <label className={`flex items-center gap-2 text-sm font-medium mb-2 flex-shrink-0 ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            <FileText className="w-4 h-4" />
            Resume Medis (Free Text)
          </label>
          <textarea
            value={freeText}
            onChange={(e) => onFreeTextChange(e.target.value)}
            placeholder="Example: Pasien Pneumonia berat (J18.9) dengan saturasi oksigen rendah dirawat 5 hari. Pemberian antibiotik Ceftriaxone 2x1g IV, Azithromycin 1x500mg PO, dan terapi oksigen nasal kanul 3 liter/menit. Dilakukan foto thorax dan pemeriksaan lab lengkap."
            className={`w-full px-4 py-3 rounded-lg border flex-1 resize-none ${
              isDark
                ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
                : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
            } backdrop-blur-sm focus:outline-none focus:ring-2 ${
              isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
            } transition-all duration-300`}
          />
          <p className={`text-xs mt-2 flex-shrink-0 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
            AI akan otomatis memisahkan diagnosis, tindakan, dan obat dari teks ini
          </p>
        </div>
        <button
          onClick={onGenerate}
          disabled={isLoading || !freeText.trim() || isLimitReached}
          className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all duration-300 flex-shrink-0 ${
            isLimitReached
              ? 'bg-gray-400 cursor-not-allowed'
              : isDark
              ? 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500'
              : 'bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800'
          } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]`}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin" />
              Sedang menganalisis...
            </span>
          ) : isLimitReached ? (
            <span className="flex items-center justify-center gap-2">
              🚫 Limit Harian Tercapai
            </span>
          ) : (
            'Generate AI Insight'
          )}
        </button>
      </div>
    );
  }

  // Mode: form - 3 separate fields
  return (
    <div className="flex flex-col h-full gap-3">
      <div className="flex-1 flex flex-col gap-3 overflow-y-auto min-h-0">
        <div className="space-y-2 flex-shrink-0">
          <label className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            <FileText className="w-4 h-4" />
            Diagnosis
          </label>
          <input
            type="text"
            value={diagnosis}
            onChange={(e) => onDiagnosisChange(e.target.value)}
            placeholder="Masukkan diagnosis pasien..."
            className={`w-full px-4 py-2.5 rounded-lg border ${
              isDark
                ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
                : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
            } backdrop-blur-sm focus:outline-none focus:ring-2 ${
              isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
            } transition-all duration-300`}
          />
        </div>

        <div className="space-y-2 flex-shrink-0">
          <label className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            <Activity className="w-4 h-4" />
            Tindakan
          </label>
          <input
            type="text"
            value={procedure}
            onChange={(e) => onProcedureChange(e.target.value)}
            placeholder="Masukkan tindakan medis yang dilakukan..."
            className={`w-full px-4 py-2.5 rounded-lg border ${
              isDark
                ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
                : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
            } backdrop-blur-sm focus:outline-none focus:ring-2 ${
              isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
            } transition-all duration-300`}
          />
        </div>

        <div className="space-y-2 flex-shrink-0">
          <label className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            <Pill className="w-4 h-4" />
            Obat
          </label>
          <input
            type="text"
            value={medication}
            onChange={(e) => onMedicationChange(e.target.value)}
            placeholder="Masukkan daftar obat yang diresepkan..."
            className={`w-full px-4 py-2.5 rounded-lg border ${
              isDark
                ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
                : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
            } backdrop-blur-sm focus:outline-none focus:ring-2 ${
              isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
            } transition-all duration-300`}
          />
        </div>
      </div>

      <button
        onClick={onGenerate}
        disabled={isLoading || !diagnosis.trim() || !procedure.trim() || !medication.trim() || isLimitReached}
        className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all duration-300 flex-shrink-0 ${
          isLimitReached
            ? 'bg-gray-400 cursor-not-allowed'
            : isDark
            ? 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500'
            : 'bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800'
        } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin" />
            Sedang menganalisis...
          </span>
        ) : isLimitReached ? (
          <span className="flex items-center justify-center gap-2">
            🚫 Limit Harian Tercapai
          </span>
        ) : (
          'Generate AI Insight'
        )}
      </button>
    </div>
  );
}
