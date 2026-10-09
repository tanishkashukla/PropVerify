import React from 'react';
import { documentTypeLabel } from '../constants/documentTypes';
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ArrowLeft,
  XCircle,
  Layers,
  FileSpreadsheet,
  ChevronRight
} from 'lucide-react';
import ReportSection from './ReportSection';

const FIELD_LABELS_MAP = {
  survey_gat_number: 'Survey / Gat Number',
  owner_name: 'Owner Name',
  seller_name: 'Seller Name',
  buyer_name: 'Buyer Name',
  property_address: 'Property Address',
  property_area: 'Property Area',
  registration_number: 'Registration Number',
  document_date: 'Document Date',
  document_number: 'Document Reference Number'
};

const formatFieldLabel = (field) => {
  if (!field) return '';
  return FIELD_LABELS_MAP[field] || field.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
};

export default function VerificationDashboard({
  result,
  onReset,
  onSelectMismatch,
  className = ''
}) {
  if (!result) return null;

  const isIssues = result.overall_status === 'ISSUES_FOUND';
  const isError = result.overall_status === 'ERROR';
  const isIncomplete = result.overall_status === 'PROCESSING_INCOMPLETE' || isError;
  const isClean = result.overall_status === 'VERIFIED' && !isIncomplete && result.mismatches.length === 0 && result.missing_documents.length === 0;

  const requiredDocsList = result.required_documents || [];
  const providedDocsList = result.provided_documents || [];
  const missingDocsList = result.missing_documents || [];
  const matchesList = result.matches || [];
  const mismatchesList = result.mismatches || [];
  const missingFieldsList = result.missing_fields || [];
  const processedDocuments = result.processed_documents || [];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 1. OVERALL STATUS BANNER */}
      <div
        className={`p-6 rounded-xl border shadow-sm transition-all ${
          isClean
            ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950'
            : isIssues
            ? 'bg-amber-50/80 border-amber-200 text-amber-950'
            : isIncomplete
            ? 'bg-amber-50/80 border-amber-200 text-amber-950'
            : 'bg-blue-50/80 border-blue-200 text-blue-950'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start md:items-center gap-3.5">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center text-white shadow-md flex-shrink-0 ${
                isClean
                  ? 'bg-emerald-600'
                  : isIssues
                  ? 'bg-amber-600'
                  : isIncomplete
                  ? 'bg-amber-600'
                  : 'bg-blue-600'
              }`}
            >
              {isClean ? (
                <ShieldCheck className="w-7 h-7" />
              ) : (
                <ShieldAlert className="w-7 h-7" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-xl font-bold tracking-tight">
                  {isError
                    ? 'Extraction Failed'
                    : isClean
                    ? '✓ Verification Passed'
                    : isIssues
                    ? '⚠ Issues Found'
                    : isIncomplete
                    ? 'Verification Needs Review'
                    : '⚠ Missing Documents'}
                </h2>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                    isClean
                      ? 'bg-emerald-200 text-emerald-900'
                      : isIssues
                      ? 'bg-amber-200 text-amber-900'
                      : isIncomplete
                      ? 'bg-amber-200 text-amber-900'
                      : 'bg-blue-200 text-blue-900'
                  }`}
                >
                  {result.overall_status}
                </span>
              </div>
              <p className="text-xs opacity-80 mt-1">
                {isError
                  ? 'Document extraction could not be completed. Review the error below and try again.'
                  : isClean
                  ? 'No inconsistencies detected across all submitted property documents.'
                  : `Analyzed ${result.documents_processed} document(s). Review detected field mismatches and warnings below.`}
              </p>
            </div>
          </div>

          {onReset && (
            <button
              type="button"
              onClick={onReset}
              className="px-4 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm cursor-pointer transition-colors self-start md:self-auto"
            >
              <ArrowLeft className="w-4 h-4" /> Start New Verification
            </button>
          )}
        </div>
      </div>

      {/* PDF REPORT GENERATION SECTION */}
      <ReportSection result={result} />

      {result.warnings?.length > 0 && (
        <div className="p-5 rounded-xl border border-amber-200 bg-amber-50 text-amber-950 space-y-2">
          <h3 className="text-sm font-semibold flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Processing Warnings</h3>
          <ul className="list-disc pl-5 space-y-1 text-xs">{result.warnings.map((warning, index) => <li key={`${index}-${warning}`}>{warning}</li>)}</ul>
        </div>
      )}

      {/* 2. SUMMARY CARDS GRID */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Documents Processed</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{result.documents_processed}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Matches</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{matchesList.length}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Mismatches</p>
          <p className="text-2xl font-bold text-red-600 mt-1">{mismatchesList.length}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Missing Documents</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{missingDocsList.length}</p>
        </div>
      </div>

      {/* 3. REQUIRED DOCUMENTS STATUS SECTION */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-600" /> Required Documents Status
          </h3>
          <span className="text-xs text-slate-500">
            {requiredDocsList.length - missingDocsList.length} of {requiredDocsList.length} Provided
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {requiredDocsList.map((docType) => {
            const missingItem = missingDocsList.find((m) => m.expected_document_type === docType);
            const isMissing = !!missingItem;
            const isProvided = providedDocsList.includes(docType);

            return (
              <div
                key={docType}
                onClick={() => isMissing && onSelectMismatch && onSelectMismatch(missingItem)}
                className={`p-3 rounded-lg border flex items-center justify-between text-xs font-medium transition-all ${
                  isMissing
                    ? 'bg-amber-50 border-amber-200 text-amber-900 cursor-pointer hover:bg-amber-100/70'
                    : isProvided
                    ? 'bg-emerald-50/60 border-emerald-200 text-emerald-900'
                    : 'bg-slate-50 border-slate-200 text-slate-600'
                }`}
              >
                <div className="flex items-center gap-2">
                  {isMissing ? (
                    <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  )}
                  <span>{documentTypeLabel(docType)}</span>
                </div>

                <div className="flex items-center gap-1">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${
                      isMissing
                        ? 'bg-amber-200 text-amber-900'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {isMissing ? 'Missing' : 'Provided'}
                  </span>
                  {isMissing && <ChevronRight className="w-3.5 h-3.5 text-amber-700" />}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {processedDocuments.length > 0 && (
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2"><FileText className="w-4 h-4 text-blue-600" /> Extracted Information</h3>
          {processedDocuments.map((document) => {
            const fields = Object.entries(document.extracted_data || {}).filter(([key, value]) => key !== 'document_type' && value);
            return <article key={document.file_name} className="border border-slate-200 rounded-lg p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div><h4 className="text-xs font-semibold text-slate-900">{documentTypeLabel(document.document_type_detected)}</h4><p className="text-[11px] text-slate-500 mt-0.5">{document.file_name}</p></div>
                <div className="flex gap-2 text-[10px] font-semibold">
                <span className={`px-2 py-1 rounded ${document.ai_used ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-800'}`}>{document.ai_used ? 'AI extraction' : 'Deterministic extraction'}</span>
                  {document.ocr_used && <span className="px-2 py-1 rounded bg-blue-50 text-blue-800">OCR used</span>}
                </div>
              </div>
              {fields.length ? <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2">{fields.map(([key, value]) => <div key={key} className="rounded bg-slate-50 px-3 py-2"><dt className="text-[10px] text-slate-500">{formatFieldLabel(key)}</dt><dd className="text-xs text-slate-900 font-medium break-words">{value}</dd></div>)}</dl> : <p className="text-xs text-amber-800">No structured fields were extracted from this document.</p>}
            </article>;
          })}
        </div>
      )}

      {/* 4. MISMATCH HIGHLIGHT SECTION */}
      {mismatchesList.length > 0 && (
        <div className="bg-white p-6 rounded-xl border border-red-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-red-100">
            <h3 className="text-sm font-semibold text-red-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600" /> Conflicting Field Mismatches Detected
            </h3>
            <span className="text-xs text-red-700 font-medium">Click any mismatch for detailed view</span>
          </div>

          <div className="space-y-4">
            {mismatchesList.map((mismatch, idx) => (
              <div
                key={idx}
                onClick={() => onSelectMismatch && onSelectMismatch(mismatch)}
                className="p-4 bg-red-50/50 border border-red-200 hover:border-red-300 hover:bg-red-50 rounded-xl space-y-3 cursor-pointer transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-red-900 text-sm capitalize group-hover:text-blue-600 transition-colors">
                      {mismatch.field.replace(/_/g, ' ')}
                    </span>
                    <span className="px-2 py-0.5 bg-red-200 text-red-900 font-bold rounded text-[10px] uppercase tracking-wider">
                      ⚠ MISMATCH
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 bg-red-100 text-red-800 font-bold rounded-full text-[10px] uppercase">
                      Severity: {mismatch.severity}
                    </span>
                    <ChevronRight className="w-4 h-4 text-red-600 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </div>

                <p className="text-xs text-red-800 font-medium">{mismatch.message}</p>

                <div className="bg-white p-3.5 rounded-lg border border-red-100 space-y-2">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                    Extracted Values Across Uploaded Documents:
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {Object.entries(mismatch.values || {}).map(([file, val]) => {
                      const isConflicting = (mismatch.conflicting_documents || []).includes(file);
                      return (
                        <div
                          key={file}
                          className={`flex items-center justify-between p-2.5 rounded border text-xs ${
                            isConflicting
                              ? 'bg-red-100/70 border-red-300 text-red-950 font-semibold'
                              : 'bg-slate-50 border-slate-200 text-slate-800'
                          }`}
                        >
                          <span className="font-medium truncate">{file}:</span>
                          <span className={`font-mono text-xs ${isConflicting ? 'text-red-700 font-bold' : 'text-slate-900'}`}>
                            {val} {isConflicting && '⚠'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. VERIFICATION RESULTS TABLE */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 pb-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-blue-600" /> Field Verification Summary Table
          </h3>
          <span className="text-xs text-slate-500">
            {matchesList.length + mismatchesList.length + missingFieldsList.length} Fields Evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-500 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-200">
                <th className="py-3 px-4">Field</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Verification Details</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {mismatchesList.map((mismatch) => (
                <tr
                  key={mismatch.field}
                  onClick={() => onSelectMismatch && onSelectMismatch(mismatch)}
                  className="bg-red-50/40 hover:bg-red-50 transition-colors cursor-pointer group"
                >
                  <td className="py-3.5 px-4 font-semibold text-red-900 group-hover:text-blue-600">
                    {formatFieldLabel(mismatch.field)}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2.5 py-1 bg-red-100 text-red-800 font-bold rounded-md text-[10px] inline-flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3 text-red-600" /> MISMATCH
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-red-900 font-medium">
                    {mismatch.message}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <span className="text-blue-600 font-semibold inline-flex items-center gap-1 group-hover:underline">
                      Inspect <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </td>
                </tr>
              ))}

              {matchesList.map((match) => (
                <tr key={match.field} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-medium text-slate-900">
                    {formatFieldLabel(match.field)}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 font-bold rounded-md text-[10px] inline-flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> MATCH
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-700 font-mono truncate max-w-md">
                    {match.matched_value}
                  </td>
                  <td className="py-3.5 px-4 text-right text-slate-400">
                    —
                  </td>
                </tr>
              ))}

              {missingFieldsList.map((mf, i) => (
                <tr key={i} className="bg-slate-50/60 text-slate-500">
                  <td className="py-3.5 px-4 font-medium text-slate-600">
                    {formatFieldLabel(mf.field)}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2.5 py-1 bg-slate-200 text-slate-700 font-bold rounded-md text-[10px] inline-flex items-center gap-1">
                      <XCircle className="w-3 h-3 text-slate-500" /> MISSING
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-500">
                    {mf.message}
                  </td>
                  <td className="py-3.5 px-4 text-right text-slate-400">
                    —
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 6. MISSING DOCUMENTS SECTION */}
      {missingDocsList.length > 0 ? (
        <div className="bg-white p-6 rounded-xl border border-amber-200 shadow-sm space-y-3">
          <h3 className="text-sm font-semibold text-amber-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" /> Missing Required Documents
          </h3>
          <div className="space-y-2">
            {missingDocsList.map((missing, idx) => (
              <div
                key={idx}
                onClick={() => onSelectMismatch && onSelectMismatch(missing)}
                className="p-3.5 bg-amber-50 border border-amber-200 hover:bg-amber-100/70 rounded-lg flex items-center justify-between text-xs text-amber-900 cursor-pointer transition-colors group"
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span className="font-semibold">{documentTypeLabel(missing.expected_document_type)}</span> — {missing.message}
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-amber-200 text-amber-900 font-bold rounded text-[10px] uppercase">
                    {missing.severity}
                  </span>
                  <ChevronRight className="w-4 h-4 text-amber-700 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-2 text-xs text-emerald-800 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>✓ All selected required documents were provided in the upload set.</span>
        </div>
      )}

      {/* 7. CLEAN / VERIFIED STATE */}
      {isClean && (
        <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-4 text-emerald-950">
          <div className="w-12 h-12 rounded-full bg-emerald-600 text-white flex items-center justify-center flex-shrink-0 shadow-md">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-base font-bold">✓ Documents Verified</h3>
            <p className="text-xs text-emerald-800 mt-0.5">
              No inconsistencies detected in the submitted property documents. All common fields match consistently across records.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
