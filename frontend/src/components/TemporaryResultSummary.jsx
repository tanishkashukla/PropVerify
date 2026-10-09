import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, CheckCircle2, FileText, ArrowLeft } from 'lucide-react';
import { documentTypeLabel } from '../constants/documentTypes';

export default function TemporaryResultSummary({
  result,
  onReset,
  className = ''
}) {
  if (!result) return null;

  const isIssues = result.overall_status !== 'VERIFIED';

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Banner */}
      <div className={`p-6 rounded-xl border shadow-sm ${
        isIssues ? 'bg-amber-50/70 border-amber-200 text-amber-950' : 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white shadow-md ${
              isIssues ? 'bg-amber-600' : 'bg-emerald-600'
            }`}>
              {isIssues ? <ShieldAlert className="w-7 h-7" /> : <ShieldCheck className="w-7 h-7" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold">
                  {isIssues
                    ? 'Issues Found During Verification'
                    : 'Verification Passed Successfully'}
                </h2>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                  isIssues ? 'bg-amber-200 text-amber-900' : 'bg-emerald-200 text-emerald-900'
                }`}>
                  {result.overall_status}
                </span>
              </div>
              <p className="text-xs opacity-80 mt-1">
                Processed {result.documents_processed} document{result.documents_processed === 1 ? '' : 's'} against {result.required_documents?.length || 0} required document type(s).
              </p>
            </div>
          </div>

          {onReset && (
            <button
              type="button"
              onClick={onReset}
              className="px-4 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm cursor-pointer transition-colors"
            >
              <ArrowLeft className="w-4 h-4" /> New Verification
            </button>
          )}
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Processed</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{result.documents_processed}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Matches</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{result.matches?.length || 0}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Mismatches</p>
          <p className="text-2xl font-bold text-red-600 mt-1">{result.mismatches?.length || 0}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Missing Docs</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{result.missing_documents?.length || 0}</p>
        </div>
      </div>

      {/* Provided Documents List */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-600" /> Detected Document Types Provided
        </h3>
        <div className="flex flex-wrap gap-2">
          {result.provided_documents?.map((docType) => (
            <span
              key={docType}
              className="px-3 py-1 bg-blue-50 text-blue-800 border border-blue-200 rounded-lg text-xs font-medium flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" /> {documentTypeLabel(docType)}
            </span>
          ))}
        </div>
      </div>

      {/* Mismatches Breakdown */}
      {result.mismatches && result.mismatches.length > 0 && (
        <div className="bg-white p-5 rounded-xl border border-red-200 shadow-sm space-y-4">
          <h3 className="text-sm font-semibold text-red-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" /> Conflicting Field Mismatches Detected
          </h3>

          <div className="space-y-3">
            {result.mismatches.map((mismatch, idx) => (
              <div key={idx} className="p-4 bg-red-50/50 border border-red-200 rounded-lg space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-red-900 text-sm capitalize">
                    Field: {mismatch.field.replace(/_/g, ' ')}
                  </span>
                  <span className="px-2 py-0.5 bg-red-100 text-red-800 font-bold rounded text-[10px] uppercase">
                    Severity: {mismatch.severity}
                  </span>
                </div>

                <p className="text-red-800 font-medium">{mismatch.message}</p>

                {/* Values across documents */}
                <div className="bg-white p-3 rounded border border-red-100 space-y-1.5">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Values Found Across Documents:</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {Object.entries(mismatch.values || {}).map(([file, val]) => (
                      <div key={file} className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-200 text-xs">
                        <span className="font-medium text-slate-700 truncate">{file}:</span>
                        <span className={`font-mono font-bold ${(mismatch.conflicting_documents || []).includes(file) ? 'text-red-700 bg-red-100 px-1.5 py-0.5 rounded' : 'text-slate-900'}`}>
                          {val}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing Documents Warning */}
      {result.missing_documents && result.missing_documents.length > 0 && (
        <div className="bg-white p-5 rounded-xl border border-amber-200 shadow-sm space-y-3">
          <h3 className="text-sm font-semibold text-amber-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" /> Missing Required Documents
          </h3>
          <div className="space-y-2">
            {result.missing_documents.map((missing, idx) => (
              <div key={idx} className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between text-xs text-amber-900">
                <span className="font-medium">⚠ {missing.message}</span>
                <span className="px-2 py-0.5 bg-amber-200 text-amber-900 font-bold rounded text-[10px] uppercase">
                  {missing.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
