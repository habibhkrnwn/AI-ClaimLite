import { AnalysisResult } from '../lib/supabase';
import {
  Activity,
  FileText,
  Pill,
  BarChart3,
} from 'lucide-react';

interface ResultsPanelProps {
  result: AnalysisResult | null;
  isDark: boolean;
}

export default function ResultsPanel({ result, isDark }: ResultsPanelProps) {
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

  const cleanStatus = (status: string) =>
  status?.replace(/[✔️⚠️❌]/g, "").trim(); // buang emoji duplikat dari backend

  const getStatusIcon = (status: string) => {
    if (!status) return "➖";

    const s = cleanStatus(status).toLowerCase();
    if (s.includes("sesuai")) return "✔️";
    if (s.includes("parsial")) return "⚠️";
    if (s.includes("tidak")) return "❌";
    return "➖";
  };

  const cardClass = `rounded-xl p-5 ${
    isDark
      ? 'bg-slate-800/40 border border-cyan-500/20'
      : 'bg-white/60 border border-blue-100'
  } backdrop-blur-md shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]`;

  return (
    <div className="grid grid-cols-2 gap-4 overflow-y-auto max-h-full pr-2">

      {/* ==================== CP NASIONAL RINGKAS ====================== */}
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

      {/* ====================== DOKUMEN WAJIB ========================== */}
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
      <div
        className={`rounded-xl p-5 mb-6 col-span-2 ${
          isDark
            ? "bg-slate-800/40 border border-cyan-500/20"
            : "bg-white/60 border border-blue-100"
        } backdrop-blur-md shadow-lg`}
      >

        {/* HEADER BARU — sejajar */}
        <div className="flex items-center justify-between mb-4">

          {/* LEFT: Icon + Title */}
          <div className="flex items-center gap-2">
            <Pill className={`w-5 h-5 ${isDark ? "text-cyan-300" : "text-blue-600"}`} />

            <h3
              className={`text-lg font-semibold ${
                isDark ? "text-cyan-300" : "text-blue-700"
              }`}
            >
              Validasi Fornas
            </h3>
          </div>

          {/* RIGHT: Badge + Ringkasan */}
          <div className="flex items-center gap-4">

            {/* BADGE */}
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

            {/* RINGKASAN */}
            <p className={`text-sm ${isDark ? "text-slate-300" : "text-gray-600"}`}>
              {result.fornasSummary.sesuai}/{result.fornasSummary.total_obat} obat sesuai Fornas (
              {Math.round(
                (result.fornasSummary.sesuai /
                  result.fornasSummary.total_obat) *
                  100
              )}
              %)
            </p>
          </div>
        </div>

        {/* TABEL FORNAS (tetap seperti sebelumnya) */}
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

            <tbody
              className={`divide-y ${
                isDark ? "divide-slate-700 text-slate-200" : "divide-gray-200 text-gray-700"
              }`}
            >
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

        {/* SUMMARY BAWAH — sejajar horizontal */}
        <div
          className={`mt-4 flex flex-wrap items-center justify-between gap-4 text-sm ${
            isDark ? "text-slate-300" : "text-gray-700"
          }`}
        >
          <p>
            📘 <strong>Sumber Regulasi:</strong>{" "}
            {result.fornasList
              ?.map((item: any) => item.sumber_regulasi)
              .filter((v: any, i: number, a: any[]) => v && a.indexOf(v) === i)
              .join(" • ") || "-"}
          </p>

          <p>
            📅 <strong>Update:</strong> {result.fornasSummary.update_date}
          </p>

          <p>
            📊 <strong>Status Data:</strong> {result.fornasSummary.status_database}
          </p>
        </div>
      </div>

      {/* ================== Konsistensi Klinis ================== */}
      <div
        className={`rounded-xl p-5 mb-6 col-span-2 ${
          isDark
            ? "bg-slate-800/40 border border-cyan-500/20"
            : "bg-white/60 border border-blue-100"
        } backdrop-blur-md shadow-lg`}
      >
        {/* HEADER — FIX */}
        <div className="flex items-center gap-2 mb-4">
          <Activity className={`w-5 h-5 mt-[2px] ${isDark ? "text-cyan-400" : "text-blue-600"}`} />

          <h3
            className={`text-lg font-semibold ${
              isDark ? "text-cyan-300" : "text-blue-700"
            }`}
          >
            Konsistensi Klinis
          </h3>
        </div>
          {[
            {
              title: "Validasi Diagnosis – Tindakan",
              data: result.consistency?.dx_tx,
            },
            {
              title: "Validasi Diagnosis – Obat",
              data: result.consistency?.dx_drug,
            },
            {
              title: "Validasi Tindakan – Obat",
              data: result.consistency?.tx_drug,
            },
          ].map((item, idx) => (
            <div key={idx} className="pb-6 mb-6 border-b border-slate-600/30">

              {/* TABEL 2 KOLOM */}
              <div
                className={`
                  overflow-x-auto rounded-xl border
                  ${isDark ? "border-slate-700 bg-slate-800/30" : "border-gray-200 bg-white/40"}
                `}
              >
                <table className="min-w-full text-sm table-fixed">

                  {/* HEADER */}
                  <thead
                    className={
                      isDark
                        ? "bg-slate-700/60 text-slate-100"
                        : "bg-blue-50 text-blue-900"
                    }
                  >
                    <tr>
                      {/* Lebar 33% */}
                      <th className="w-1/3 px-4 py-2 text-left font-semibold">
                        {item.title}
                      </th>
                      {/* Lebar 67% */}
                      <th className="w-2/3 px-4 py-2 text-left font-semibold">
                        Catatan
                      </th>
                    </tr>
                  </thead>

                  {/* BODY */}
                  <tbody
                    className={`
                      ${isDark ? "text-slate-200" : "text-gray-700"}
                      divide-y ${isDark ? "divide-slate-700" : "divide-gray-200"}
                    `}
                  >
                    <tr
                      className={`${
                        isDark ? "hover:bg-slate-800/40" : "hover:bg-gray-50"
                      } transition`}
                    >
                      {/* STATUS */}
                      <td className="align-top px-4 py-[14px]">
                        <span className="font-medium">Status:</span>{" "}
                        <span className="inline-flex items-center gap-1 font-medium">
                          {getStatusIcon(item.data?.status)}
                          {cleanStatus(item.data?.status) ?? "-"}
                        </span>
                      </td>

                      {/* CATATAN (RAPI, KOTAK, ALIGNED PERFECTLY) */}
                      <td className="align-top px-4 py-3">
                        <div
                          className={`
                            rounded-lg px-3 py-2 leading-tight
                            ${isDark ? "bg-slate-900/30 border border-slate-700" : "bg-white/70 border border-gray-200"}
                          `}
                        >
                          {item.data?.catatan || "-"}
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          ))}

        {/* TINGKAT KONSISTENSI */}
        <p
          className={`font-semibold mb-2 ${
            isDark ? "text-slate-200" : "text-gray-900"
          }`}
        >
          Tingkat Konsistensi:{" "}
          <span className="font-medium">
            {result.consistency?.tingkat ?? "-"}
          </span>
        </p>

        {/* PROGRESS BAR */}
        {(() => {
          const tingkat = (result.consistency?.tingkat ?? "-").toLowerCase();
          let percent = 0;
          let color =
            isDark ? "bg-red-600" : "bg-red-500";

          if (tingkat === "tinggi") {
            percent = 100;
            color = isDark ? "bg-green-600" : "bg-green-500";
          } else if (tingkat === "sedang") {
            percent = 60;
            color = isDark ? "bg-yellow-500" : "bg-yellow-400";
          } else {
            percent = 30;
          }

          return (
            <div
              className={`w-full h-3 rounded-full overflow-hidden ${
                isDark ? "bg-slate-700/50" : "bg-gray-200"
              }`}
            >
              <div
                className={`h-full ${color} transition-all duration-500`}
                style={{ width: `${percent}%` }}
              ></div>
            </div>
          );
        })()}
      </div> 
    </div>
  );
}
