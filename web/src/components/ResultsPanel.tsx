import { AnalysisResult } from '../lib/supabase';
import {
  Code,
  CheckCircle,
  AlertTriangle,
  XCircle,
  // Activity,
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

    const cardClass = `rounded-xl p-5 ${
      isDark
        ? 'bg-slate-800/40 border border-cyan-500/20'
        : 'bg-white/60 border border-blue-100'
    } backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]`;

    const headerClass = isDark
      ? "font-semibold text-cyan-300"
      : "font-semibold text-blue-700";

    return (
      <div className="space-y-4 overflow-y-auto max-h-full pr-2">

        {/* CP Nasional Ringkas */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <FileText className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
            <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
              CP Nasional Ringkas
            </h3>
          </div>
          <ul className="space-y-2 pl-1">
            {result.cpNasional.map((item, idx) => (
              <li
                key={idx}
                className={`flex items-start gap-2 text-sm leading-relaxed ${
                  isDark ? 'text-slate-300' : 'text-gray-700'
                }`}
              >
                <div
                  className={`w-1.5 h-1.5 mt-1 rounded-full ${
                    isDark ? 'bg-cyan-400' : 'bg-blue-500'
                  }`}
                />
                <span>
                  {item.tahap && <strong>{item.tahap}:</strong>} {item.keterangan}
                </span>
              </li>
            ))}
          </ul>
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

        {/* =======================  FORNAS SECTION ======================= */}
        <div className={cardClass}>
          {/* Header */}
          <div className="flex items-center gap-2 mb-4">
            <Pill className={`${isDark ? "text-cyan-300" : "text-blue-600"}`} />
            <h3 className={headerClass}>Validasi Fornas</h3>
          </div>

          {/* Status Badge */}
          <div className="mb-3">
            <span
              className={`
                px-3 py-1 rounded-full text-xs font-semibold
                ${
                  result.fornasSummary.sesuai > 0
                    ? (isDark ? "bg-green-900 text-green-200" : "bg-green-100 text-green-700")
                    : result.fornasSummary.perlu_justifikasi > 0
                    ? (isDark ? "bg-yellow-900 text-yellow-200" : "bg-yellow-100 text-yellow-700")
                    : (isDark ? "bg-red-900 text-red-200" : "bg-red-100 text-red-700")
                }
              `}
            >
              {result.fornasSummary.sesuai > 0
                ? "SESUAI"
                : result.fornasSummary.perlu_justifikasi > 0
                ? "PERLU JUSTIFIKASI"
                : "TIDAK SESUAI"}
            </span>

            <p className={`text-sm mt-1 ${isDark ? "text-slate-300" : "text-gray-600"}`}>
              {result.fornasSummary.sesuai}/{result.fornasSummary.total_obat} obat sesuai Fornas (
              {Math.round(
                (result.fornasSummary.sesuai / result.fornasSummary.total_obat) * 100
              )}%)
            </p>
          </div>

          {/* TABEL FORNAS */}
          <div
            className={`
              overflow-x-auto rounded-xl border
              ${isDark ? "border-slate-700 bg-slate-800/30" : "border-gray-200 bg-white/40"}
              shadow-inner
            `}
          >
            <table className="min-w-full text-sm">
              <thead className={isDark ? "bg-slate-700/60 text-slate-100" : "bg-blue-50 text-blue-900"}>
                <tr>
                  <th className="px-4 py-2 text-left font-semibold">No</th>
                  <th className="px-4 py-2 text-left font-semibold">Nama Obat</th>
                  <th className="px-4 py-2 text-left font-semibold">Kelas Terapi</th>
                  <th className="px-4 py-2 text-left font-semibold">Status AI</th>
                  <th className="px-4 py-2 text-left font-semibold">Catatan AI</th>
                </tr>
              </thead>

              <tbody className={`divide-y ${isDark ? "divide-slate-700 text-slate-200" : "divide-gray-200 text-gray-700"}`}>
                {result.fornasList?.map((item: any, index: number) => (
                  <tr
                    key={index}
                    className={`${isDark ? "hover:bg-slate-800/50" : "hover:bg-gray-50"} transition`}
                  >
                    <td className="px-4 py-2">{index + 1}</td>
                    <td className="px-4 py-2 capitalize">{item.nama_obat}</td>
                    <td className="px-4 py-2 whitespace-pre-line">{item.kelas_terapi}</td>
                    <td className="px-4 py-2 font-medium">{item.status_fornas}</td>
                    <td className="px-4 py-2">{item.catatan_ai}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* SUMMARY REGULASI */}
          <div className="mt-4 space-y-1 text-sm">
            <p className={`${isDark ? "text-slate-300" : "text-gray-600"}`}>
              📘 <strong>Sumber Regulasi:</strong>{" "}
              {result.fornasList
                ?.map((item: any) => item.sumber_regulasi)
                .filter((v: any, i: number, a: any[]) => v && a.indexOf(v) === i)
                .join(" • ") || "-"}
            </p>

            <p className={`${isDark ? "text-slate-300" : "text-gray-600"}`}>
              📅 <strong>Update:</strong> {result.fornasSummary.update_date}
            </p>

            <p className={`${isDark ? "text-slate-300" : "text-gray-600"}`}>
              📊 <strong>Status Data:</strong> {result.fornasSummary.status_database}
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

        {/* ============================ 🔵 KONSISTENSI KLINIS =============================== */}
        <div className={cardClass}>
          <div className="flex items-center gap-2 mb-3">
            <Pill className={isDark ? "bg-blue-500/20 text-blue-300" : "bg-blue-100 text-blue-600"} />
            <h3 className={isDark ? "text-blue-300" : "text-blue-600"}>Konsistensi Klinis</h3>
          </div>

          {/* === BLOK VALIDASI === */}
          <div className={`space-y-4 ${isDark ? "text-slate-300" : "text-gray-700"}`}>

            {/* DX – TX */}
            <div className={isDark ? "border-b border-slate-700 pb-3" : "border-b border-gray-300 pb-3"}>
              <p className="font-semibold">Validasi Diagnosis – Tindakan</p>
              <p>Status: {result.consistency.dx_tx?.status || "-"}</p>
              <p>Catatan: {result.consistency.dx_tx?.catatan || "-"}</p>
            </div>

            {/* DX – DRUG */}
            <div className={isDark ? "border-b border-slate-700 pb-3" : "border-b border-gray-300 pb-3"}>
              <p className="font-semibold">Validasi Diagnosis – Obat</p>
              <p>Status: {result.consistency.dx_drug?.status || "-"}</p>
              <p>Catatan: {result.consistency.dx_drug?.catatan || "-"}</p>
            </div>

            {/* TX – DRUG */}
            <div className={isDark ? "border-b border-slate-700 pb-3" : "border-b border-gray-300 pb-3"}>
              <p className="font-semibold">Validasi Tindakan – Obat</p>
              <p>Status: {result.consistency.tx_drug?.status || "-"}</p>
              <p>Catatan: {result.consistency.tx_drug?.catatan || "-"}</p>
            </div>
          </div>

          {/* === TINGKAT KONSISTENSI === */}
          <div className="mt-4">
            <p className={isDark ? "text-slate-300 mb-1" : "text-gray-700 mb-1"}>
              <strong>Tingkat Konsistensi:</strong> {result.consistency.tingkat || "-"}
            </p>

            {/* PROGRESS BAR MENGIKUTI LEVEL */}
            {(() => {
              const tingkat = (result.consistency.tingkat || "").toLowerCase();

              const barColor =
                tingkat === "tinggi"
                  ? "bg-green-500"
                  : tingkat === "sedang"
                  ? "bg-yellow-500"
                  : "bg-red-500";

              const barWidth =
                tingkat === "tinggi" ? "100%" : tingkat === "sedang" ? "60%" : "25%";

              return (
                <div className="w-full h-3 rounded-full bg-slate-700/30 overflow-hidden">
                  <div className={`h-full ${barColor}`} style={{ width: barWidth }}></div>
                </div>
              );
            })()}
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

  const headerClass = isDark
    ? "font-semibold text-cyan-300"
    : "font-semibold text-blue-700";

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
          <FileText className={`w-5 h-5 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`} />
          <h3 className={`font-semibold ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            CP Nasional Ringkas
          </h3>
        </div>
        <ul className="space-y-2 pl-1">
          {result.cpNasional.map((item, idx) => (
            <li
              key={idx}
              className={`flex items-start gap-2 text-sm leading-relaxed ${
                isDark ? 'text-slate-300' : 'text-gray-700'
              }`}
            >
              <div
                className={`w-1.5 h-1.5 mt-1 rounded-full ${
                  isDark ? 'bg-cyan-400' : 'bg-blue-500'
                }`}
              />
              <span>
                {item.tahap && <strong>{item.tahap}:</strong>} {item.keterangan}
              </span>
            </li>
          ))}
        </ul>
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

      {/* =======================  FORNAS SECTION ======================= */}
      <div className={cardClass}>
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <Pill className={`${isDark ? "text-cyan-300" : "text-blue-600"}`} />
          <h3 className={headerClass}>Validasi Fornas</h3>
        </div>

        {/* Status Badge */}
        <div className="mb-3">
          <span
            className={`
              px-3 py-1 rounded-full text-xs font-semibold
              ${
                result.fornasSummary.sesuai > 0
                  ? (isDark ? "bg-green-900 text-green-200" : "bg-green-100 text-green-700")
                  : result.fornasSummary.perlu_justifikasi > 0
                  ? (isDark ? "bg-yellow-900 text-yellow-200" : "bg-yellow-100 text-yellow-700")
                  : (isDark ? "bg-red-900 text-red-200" : "bg-red-100 text-red-700")
              }
            `}
          >
            {result.fornasSummary.sesuai > 0
              ? "SESUAI"
              : result.fornasSummary.perlu_justifikasi > 0
              ? "PERLU JUSTIFIKASI"
              : "TIDAK SESUAI"}
          </span>

          <p className={`text-sm mt-1 ${isDark ? "text-slate-300" : "text-gray-600"}`}>
            {result.fornasSummary.sesuai}/{result.fornasSummary.total_obat} obat sesuai Fornas (
            {Math.round(
              (result.fornasSummary.sesuai / result.fornasSummary.total_obat) * 100
            )}%)
          </p>
        </div>

        {/* TABEL FORNAS */}
        <div
          className={`
            overflow-x-auto rounded-xl border
            ${isDark ? "border-slate-700 bg-slate-800/30" : "border-gray-200 bg-white/40"}
            shadow-inner
          `}
        >
          <table className="min-w-full text-sm">
            <thead className={isDark ? "bg-slate-700/60 text-slate-100" : "bg-blue-50 text-blue-900"}>
              <tr>
                <th className="px-4 py-2 text-left font-semibold">No</th>
                <th className="px-4 py-2 text-left font-semibold">Nama Obat</th>
                <th className="px-4 py-2 text-left font-semibold">Kelas Terapi</th>
                <th className="px-4 py-2 text-left font-semibold">Status AI</th>
                <th className="px-4 py-2 text-left font-semibold">Catatan AI</th>
              </tr>
            </thead>

            <tbody className={`divide-y ${isDark ? "divide-slate-700 text-slate-200" : "divide-gray-200 text-gray-700"}`}>
              {result.fornasList?.map((item: any, index: number) => (
                <tr
                  key={index}
                  className={`${isDark ? "hover:bg-slate-800/50" : "hover:bg-gray-50"} transition`}
                >
                  <td className="px-4 py-2">{index + 1}</td>
                  <td className="px-4 py-2 capitalize">{item.nama_obat}</td>
                  <td className="px-4 py-2 whitespace-pre-line">{item.kelas_terapi}</td>
                  <td className="px-4 py-2 font-medium">{item.status_fornas}</td>
                  <td className="px-4 py-2">{item.catatan_ai}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* SUMMARY REGULASI */}
        <div className="mt-4 space-y-1 text-sm">
          <p className={`${isDark ? "text-slate-300" : "text-gray-600"}`}>
            📘 <strong>Sumber Regulasi:</strong>{" "}
            {result.fornasList
              ?.map((item: any) => item.sumber_regulasi)
              .filter((v: any, i: number, a: any[]) => v && a.indexOf(v) === i)
              .join(" • ") || "-"}
          </p>

          <p className={`${isDark ? "text-slate-300" : "text-gray-600"}`}>
            📅 <strong>Update:</strong> {result.fornasSummary.update_date}
          </p>

          <p className={`${isDark ? "text-slate-300" : "text-gray-600"}`}>
            📊 <strong>Status Data:</strong> {result.fornasSummary.status_database}
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

      {/* ============================ 🔵 KONSISTENSI KLINIS =============================== */}
      <div className={cardClass}>
        <div className="flex items-center gap-2 mb-3">
          <Pill className={`${isDark ? "text-cyan-300" : "text-blue-600"}`} />
          <h3 className={headerClass}>Konsistensi Klinis</h3>
        </div>

        {/* === BLOK VALIDASI === */}
        <div className={`space-y-4 ${isDark ? "text-slate-300" : "text-gray-700"}`}>

          {/* DX – TX */}
          <div className={isDark ? "border-b border-slate-700 pb-3" : "border-b border-gray-300 pb-3"}>
            <p className="font-semibold">Validasi Diagnosis – Tindakan</p>
            <p>Status: {result.consistency.dx_tx?.status || "-"}</p>
            <p>Catatan: {result.consistency.dx_tx?.catatan || "-"}</p>
          </div>

          {/* DX – DRUG */}
          <div className={isDark ? "border-b border-slate-700 pb-3" : "border-b border-gray-300 pb-3"}>
            <p className="font-semibold">Validasi Diagnosis – Obat</p>
            <p>Status: {result.consistency.dx_drug?.status || "-"}</p>
            <p>Catatan: {result.consistency.dx_drug?.catatan || "-"}</p>
          </div>

          {/* TX – DRUG */}
          <div className={isDark ? "border-b border-slate-700 pb-3" : "border-b border-gray-300 pb-3"}>
            <p className="font-semibold">Validasi Tindakan – Obat</p>
            <p>Status: {result.consistency.tx_drug?.status || "-"}</p>
            <p>Catatan: {result.consistency.tx_drug?.catatan || "-"}</p>
          </div>
        </div>

        {/* === TINGKAT KONSISTENSI === */}
        <div className="mt-4">
          <p className={isDark ? "text-slate-300 mb-1" : "text-gray-700 mb-1"}>
            <strong>Tingkat Konsistensi:</strong> {result.consistency.tingkat || "-"}
          </p>

          {/* PROGRESS BAR MENGIKUTI LEVEL */}
          {(() => {
            const tingkat = (result.consistency.tingkat || "").toLowerCase();

            const barColor =
              tingkat === "tinggi"
                ? "bg-green-500"
                : tingkat === "sedang"
                ? "bg-yellow-500"
                : "bg-red-500";

            const barWidth =
              tingkat === "tinggi" ? "100%" : tingkat === "sedang" ? "60%" : "25%";

            return (
              <div className="w-full h-3 rounded-full bg-slate-700/30 overflow-hidden">
                <div className={`h-full ${barColor}`} style={{ width: barWidth }}></div>
              </div>
            );
          })()}
        </div>
      </div>

    </div>
  );
}
