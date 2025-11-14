import { FileText, Activity, Pill } from 'lucide-react';

type InputMode = 'form' | 'text';

interface SmartInputPanelProps {
  mode: InputMode;
  diagnosis: string;
  procedure: string;
  medication: string;
  freeText: string;
  onDiagnosisChange: (value: string) => void;
  onProcedureChange: (value: string) => void;
  onMedicationChange: (value: string) => void;
  onFreeTextChange: (value: string) => void;
  onGenerate: () => Promise<void>;
  isLoading: boolean;
  isDark: boolean;
  aiUsage?: { used: number; remaining: number; limit: number } | null;
}

export default function SmartInputPanel({
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
}: SmartInputPanelProps) {
  const isLimitReached = aiUsage ? aiUsage.remaining === 0 : false;



  // Original Input Mode (Form or Text)
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
            placeholder="Example: Pasien paru2 basah dengan saturasi oksigen rendah..."
            className={`w-full px-4 py-3 rounded-lg border flex-1 resize-none ${
              isDark
                ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
                : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
            } backdrop-blur-sm focus:outline-none focus:ring-2 ${
              isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
            } transition-all duration-300`}
          />
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
          } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl`}
        >
          {isLoading ? 'Menganalisis...' : '✨ Generate AI Insight'}
        </button>
      </div>
    );
  }

  // Form Mode
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
            placeholder="Masukkan diagnosis (mis: paru2 basah)..."
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
            placeholder="Masukkan tindakan medis..."
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
            placeholder="Masukkan daftar obat..."
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
        } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl`}
      >
        {isLoading ? 'Menganalisis...' : '✨ Generate AI Insight'}
      </button>
    </div>
  );
}
