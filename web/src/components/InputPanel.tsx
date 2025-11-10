import { useState, useRef } from 'react';
import { FileText, Activity, Pill, Upload } from 'lucide-react';

type InputMode = 'text' | 'excel';

interface InputPanelProps {
  mode: InputMode;
  diagnosis: string;
  procedure: string;
  medication: string;
  onDiagnosisChange: (value: string) => void;
  onProcedureChange: (value: string) => void;
  onMedicationChange: (value: string) => void;
  onGenerate: () => void;
  isLoading: boolean;
  isDark: boolean;
}

export default function InputPanel({
  mode,
  diagnosis,
  procedure,
  medication,
  onDiagnosisChange,
  onProcedureChange,
  onMedicationChange,
  onGenerate,
  isLoading,
  isDark,
}: InputPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [excelFileName, setExcelFileName] = useState('');

  const handleExcelUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setExcelFileName(file.name);
      const reader = new FileReader();
      reader.onload = (event) => {
        const data = event.target?.result;
        console.log('Excel file loaded:', file.name);
      };
      reader.readAsArrayBuffer(file);
    }
  };

  if (mode === 'excel') {
    return (
      <div className="space-y-6 h-full flex flex-col">
        <div
          onClick={() => fileInputRef.current?.click()}
          className={`flex-1 rounded-lg border-2 border-dashed ${
            isDark
              ? 'border-cyan-500/30 bg-slate-800/20 hover:bg-slate-800/40'
              : 'border-blue-300 bg-blue-50/30 hover:bg-blue-50/50'
          } transition-all duration-300 cursor-pointer flex flex-col items-center justify-center gap-4`}
        >
          <div className={`p-4 rounded-lg ${isDark ? 'bg-cyan-500/10' : 'bg-blue-100/50'}`}>
            <Upload className={`w-10 h-10 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          </div>
          <div className="text-center">
            <p className={`font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              Upload Excel File
            </p>
            <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
              Drag and drop atau klik untuk memilih
            </p>
            <p className={`text-xs mt-2 ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>
              Format: .xlsx, .xls
            </p>
          </div>
        </div>

        {excelFileName && (
          <div className={`p-3 rounded-lg ${isDark ? 'bg-cyan-500/10 border border-cyan-500/30' : 'bg-green-50 border border-green-200'}`}>
            <p className={`text-sm font-medium ${isDark ? 'text-cyan-300' : 'text-green-700'}`}>
              File: {excelFileName}
            </p>
          </div>
        )}

        <button
          onClick={onGenerate}
          disabled={isLoading || !excelFileName}
          className={`w-full py-4 px-6 rounded-lg font-semibold text-white transition-all duration-300 ${
            isDark
              ? 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500'
              : 'bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800'
          } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]`}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin" />
              Sedang menganalisis...
            </span>
          ) : (
            'Generate AI Insight'
          )}
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls"
          onChange={handleExcelUpload}
          className="hidden"
        />
      </div>
    );
  }

  return (
    <div className="space-y-4 flex flex-col">
      <div className="space-y-2">
        <label className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          <FileText className="w-4 h-4" />
          Diagnosis
        </label>
        <input
          type="text"
          value={diagnosis}
          onChange={(e) => onDiagnosisChange(e.target.value)}
          placeholder="Masukkan diagnosis pasien..."
          className={`w-full px-4 py-3 rounded-lg border ${
            isDark
              ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
              : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
          } backdrop-blur-sm focus:outline-none focus:ring-2 ${
            isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
          } transition-all duration-300`}
        />
      </div>

      <div className="space-y-2">
        <label className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          <Activity className="w-4 h-4" />
          Tindakan
        </label>
        <input
          type="text"
          value={procedure}
          onChange={(e) => onProcedureChange(e.target.value)}
          placeholder="Masukkan tindakan medis yang dilakukan..."
          className={`w-full px-4 py-3 rounded-lg border ${
            isDark
              ? 'bg-slate-800/50 border-cyan-500/30 text-white placeholder-slate-500'
              : 'bg-white/70 border-blue-200 text-gray-900 placeholder-gray-400'
          } backdrop-blur-sm focus:outline-none focus:ring-2 ${
            isDark ? 'focus:ring-cyan-500/50' : 'focus:ring-blue-500/50'
          } transition-all duration-300`}
        />
      </div>

      <div className="space-y-2">
        <label className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
          <Pill className="w-4 h-4" />
          Obat
        </label>
        <input
          type="text"
          value={medication}
          onChange={(e) => onMedicationChange(e.target.value)}
          placeholder="Masukkan daftar obat yang diresepkan..."
          className={`w-full px-4 py-3 rounded-lg border ${
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
        disabled={isLoading || !diagnosis.trim() || !procedure.trim() || !medication.trim()}
        className={`w-full py-4 px-6 rounded-lg font-semibold text-white transition-all duration-300 flex-shrink-0 ${
          isDark
            ? 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500'
            : 'bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800'
        } disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin" />
            Sedang menganalisis...
          </span>
        ) : (
          'Generate AI Insight'
        )}
      </button>
    </div>
  );
}
