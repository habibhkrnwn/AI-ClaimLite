import { AnalysisResult } from '../lib/supabase';
import {
  Code,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Activity,
  FileText,
  Pill,
  Lightbulb,
  BarChart3,
} from 'lucide-react';

interface ResultsPanelProps {
  result: AnalysisResult | null;
  isDark: boolean;
  section?: 'severity' | 'all';
}

export default function ResultsPanel({ result, isDark, section = 'all' }: ResultsPanelProps) {
  if (!result) {
    return (
      <div className={`flex items-center justify-center h-full ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>
        <div className="text-center space-y-3">
          <BarChart3 className="w-16 h-16 mx-auto opacity-30" />
          <p className="text-sm">Hasil analisis AI akan muncul di sini</p>
        </div>
      </div>
    );
  }

  // If section is 'severity', only show severity-related cards
  if (section === 'severity') {
    const getSeverityColor = () => {
      switch (result.severity) {
        case 'ringan':
          return isDark ? 'text-green-400' : 'text-green-600';
        case 'sedang':
          return isDark ? 'text-yellow-400' : 'text-yellow-600';
        case 'berat':
          return isDark ? 'text-red-400' : 'text-red-600';
      }
    };

    const cardClass = `rounded-xl p-5 ${
      isDark
        ? 'bg-slate-800/40 border border-cyan-500/20'
        : 'bg-white/60 border border-blue-100'
    } backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]`;

    return (
      <div className="space-y-4 overflow-y-auto max-h-full pr-2">
        {/* Severity Estimation */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <Activity className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              Severity Estimation
            </h3>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-bold uppercase ${getSeverityColor()}`}>
              {result.severity}
            </span>
            <div className="flex-1 h-2 bg-slate-700/30 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  result.severity === 'ringan'
                    ? 'bg-green-500 w-1/3'
                    : result.severity === 'sedang'
                    ? 'bg-yellow-500 w-2/3'
                    : 'bg-red-500 w-full'
                } transition-all duration-500`}
              />
            </div>
          </div>
        </div>

        {/* CP Nasional Ringkas */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <FileText className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              CP Nasional Ringkas
            </h3>
          </div>
          <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
            {result.cpNasional}
          </p>
        </div>

        {/* Dokumen Wajib */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <FileText className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              Dokumen Wajib
            </h3>
          </div>
          <ul className="space-y-2">
            {result.requiredDocs.map((doc, idx) => (
              <li
                key={idx}
                className={`flex items-center gap-2 text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}
              >
                <div className={`w-1.5 h-1.5 rounded-full ${isDark ? 'bg-cyan-400' : 'bg-blue-500'}`} />
                {doc}
              </li>
            ))}
          </ul>
        </div>

        {/* Fornas */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <Pill className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>Fornas</h3>
          </div>
          <div className="space-y-2">
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
              result.fornas.status === 'sesuai'
                ? isDark ? 'bg-green-500/20 text-green-400' : 'bg-green-100 text-green-700'
                : result.fornas.status === 'tidak-sesuai'
                ? isDark ? 'bg-red-500/20 text-red-400' : 'bg-red-100 text-red-700'
                : isDark ? 'bg-yellow-500/20 text-yellow-400' : 'bg-yellow-100 text-yellow-700'
            }`}>
              {result.fornas.status.toUpperCase()}
            </span>
            <p className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
              {result.fornas.message}
            </p>
          </div>
        </div>

        {/* Insight AI */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              Insight AI
            </h3>
          </div>
          <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
            {result.aiInsight}
          </p>
        </div>

        {/* Konsistensi Klinis */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              Konsistensi Klinis
            </h3>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
                Tingkat Konsistensi
              </span>
              <span className={`text-2xl font-bold ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
                {result.consistency}%
              </span>
            </div>
            <div className="w-full h-3 bg-slate-700/30 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  result.consistency >= 80
                    ? 'bg-gradient-to-r from-green-500 to-emerald-400'
                    : result.consistency >= 60
                    ? 'bg-gradient-to-r from-yellow-500 to-orange-400'
                    : 'bg-gradient-to-r from-red-500 to-pink-400'
                } transition-all duration-1000 ease-out`}
                style={{ width: `${result.consistency}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const getValidationIcon = () => {
    switch (result.validation.status) {
      case 'valid':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'invalid':
        return <XCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getSeverityColor = () => {
    switch (result.severity) {
      case 'ringan':
        return isDark ? 'text-green-400' : 'text-green-600';
      case 'sedang':
        return isDark ? 'text-yellow-400' : 'text-yellow-600';
      case 'berat':
        return isDark ? 'text-red-400' : 'text-red-600';
    }
  };

  const getFornasBadge = () => {
    switch (result.fornas.status) {
      case 'sesuai':
        return isDark ? 'bg-green-500/20 text-green-400' : 'bg-green-100 text-green-700';
      case 'tidak-sesuai':
        return isDark ? 'bg-red-500/20 text-red-400' : 'bg-red-100 text-red-700';
      case 'perlu-review':
        return isDark ? 'bg-yellow-500/20 text-yellow-400' : 'bg-yellow-100 text-yellow-700';
    }
  };

  const cardClass = `rounded-xl p-5 ${
    isDark
      ? 'bg-slate-800/40 border border-cyan-500/20'
      : 'bg-white/60 border border-blue-100'
  } backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]`;

  const highlightCardClass = `rounded-xl p-5 ${
    isDark
      ? 'bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-400/40 shadow-lg shadow-cyan-500/10'
      : 'bg-gradient-to-br from-blue-200/40 to-blue-300/40 border border-blue-400/50 shadow-lg shadow-blue-400/10'
  } backdrop-blur-md hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]`;

  return (
    <div className="grid grid-cols-2 gap-4 overflow-y-auto max-h-full pr-2">
      <div className={highlightCardClass}>
        <div className="flex items-center gap-2 mb-3">
          <Code className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            Klasifikasi & Coding
          </h3>
        </div>
        <div className="space-y-2">
          <div>
            <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'} mb-1`}>ICD-10</p>
            <div className="flex flex-wrap gap-2">
              {result.classification.icd10.map((code, idx) => (
                <span
                  key={idx}
                  className={`px-3 py-1 rounded-full text-sm font-mono ${
                    isDark ? 'bg-cyan-500/20 text-cyan-300' : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {code}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'} mb-1`}>ICD-9</p>
            <div className="flex flex-wrap gap-2">
              {result.classification.icd9.map((code, idx) => (
                <span
                  key={idx}
                  className={`px-3 py-1 rounded-full text-sm font-mono ${
                    isDark ? 'bg-blue-500/20 text-blue-300' : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {code}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-3">
          {getValidationIcon()}
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            Validasi Klinis Cepat
          </h3>
        </div>
        <p className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
          {result.validation.message}
        </p>
      </div>

      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-3">
          <Activity className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            Severity Estimation
          </h3>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-2xl font-bold uppercase ${getSeverityColor()}`}>
            {result.severity}
          </span>
          <div className="flex-1 h-2 bg-slate-700/30 rounded-full overflow-hidden">
            <div
              className={`h-full ${
                result.severity === 'ringan'
                  ? 'bg-green-500 w-1/3'
                  : result.severity === 'sedang'
                  ? 'bg-yellow-500 w-2/3'
                  : 'bg-red-500 w-full'
              } transition-all duration-500`}
            />
          </div>
        </div>
      </div>

      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-3">
          <FileText className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            CP Nasional Ringkas
          </h3>
        </div>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
          {result.cpNasional}
        </p>
      </div>

      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-3">
          <FileText className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            Dokumen Wajib
          </h3>
        </div>
        <ul className="space-y-2">
          {result.requiredDocs.map((doc, idx) => (
            <li
              key={idx}
              className={`flex items-center gap-2 text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}
            >
              <div className={`w-1.5 h-1.5 rounded-full ${isDark ? 'bg-cyan-400' : 'bg-blue-500'}`} />
              {doc}
            </li>
          ))}
        </ul>
      </div>

      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-3">
          <Pill className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>Fornas</h3>
        </div>
        <div className="space-y-2">
          <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getFornasBadge()}`}>
            {result.fornas.status.toUpperCase()}
          </span>
          <p className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
            {result.fornas.message}
          </p>
        </div>
      </div>

      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            Insight AI
          </h3>
        </div>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
          {result.aiInsight}
        </p>
      </div>

      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-3">
          <BarChart3 className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            Konsistensi Klinis
          </h3>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className={`text-sm ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>
              Tingkat Konsistensi
            </span>
            <span className={`text-2xl font-bold ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
              {result.consistency}%
            </span>
          </div>
          <div className="w-full h-3 bg-slate-700/30 rounded-full overflow-hidden">
            <div
              className={`h-full ${
                result.consistency >= 80
                  ? 'bg-gradient-to-r from-green-500 to-emerald-400'
                  : result.consistency >= 60
                  ? 'bg-gradient-to-r from-yellow-500 to-orange-400'
                  : 'bg-gradient-to-r from-red-500 to-pink-400'
              } transition-all duration-1000 ease-out`}
              style={{ width: `${result.consistency}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
