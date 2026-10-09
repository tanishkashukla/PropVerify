import React, { useState } from 'react';
import { FileDown, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { generateReport } from '../services/api';

export default function ReportSection({
  result,
  className = ''
}) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  if (!result) return null;

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    setErrorMsg('');
    setIsSuccess(false);

    try {
      await generateReport(result);
      setIsSuccess(true);
      setTimeout(() => setIsSuccess(false), 4000);
    } catch (err) {
      console.error('Failed to generate report:', err);
      setErrorMsg(err.message || 'Failed to generate PDF report. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4 ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <FileDown className="w-5 h-5 text-blue-600" />
            PDF Verification Report
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Generate and download a formal, comprehensive PDF summary report containing all evaluation tables and mismatch details.
          </p>
        </div>

        <button
          type="button"
          onClick={handleGenerateReport}
          disabled={isGenerating}
          className={`px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm transition-all flex-shrink-0 cursor-pointer ${
            isGenerating
              ? 'bg-slate-200 text-slate-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              <span>Generating Report...</span>
            </>
          ) : (
            <>
              <FileDown className="w-4 h-4" />
              <span>Generate Verification Report</span>
            </>
          )}
        </button>
      </div>

      {/* Error State */}
      {errorMsg && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Success Download Banner */}
      {isSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-xs text-emerald-800 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>Verification report generated and downloaded successfully.</span>
        </div>
      )}
    </div>
  );
}
