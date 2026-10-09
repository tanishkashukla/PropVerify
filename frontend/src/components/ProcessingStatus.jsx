import React from 'react';
import { Loader2, CheckCircle2, AlertCircle, RefreshCw, FileText } from 'lucide-react';

export default function ProcessingStatus({
  stage = 'Uploading',
  uploadedDocs = [],
  completedDocs = [],
  currentDocName = '',
  errorMessage = '',
  onRetry,
  className = ''
}) {
  const steps = [
    { key: 'Uploading', label: 'Uploading documents' },
    { key: 'Extracting', label: 'Extracting information' },
    { key: 'Comparing', label: 'Comparing documents' },
    { key: 'Generating', label: 'Generating verification results' }
  ];

  const getStepState = (stepKey, idx) => {
    const stageMap = {
      Uploading: 0,
      Extracting: 1,
      Verifying: 2,
      Comparing: 2,
      Generating: 3,
      Completed: 4
    };
    const currentIdx = stageMap[stage] !== undefined ? stageMap[stage] : 0;
    if (stage === 'Completed' || currentIdx > idx) return 'done';
    if (currentIdx === idx && !errorMessage) return 'active';
    return 'pending';
  };

  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm p-8 max-w-xl mx-auto space-y-8 ${className}`}>
      {/* Top Card Header */}
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-100 shadow-sm">
          {errorMessage ? (
            <AlertCircle className="w-6 h-6 text-red-600" />
          ) : stage === 'Completed' ? (
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
          ) : (
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          )}
        </div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">
          {errorMessage
            ? 'Processing Error'
            : stage === 'Completed'
            ? 'Verification Complete'
            : 'Verifying Property Documents'}
        </h2>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          {errorMessage
            ? 'An issue occurred during document extraction or verification.'
            : 'Extracting document information and comparing records. Processing warnings will be shown with the results.'}
        </p>
      </div>

      {/* Error Display Banner */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 text-xs text-red-700">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1 flex-1">
            <p className="font-semibold text-red-900">Verification Failed</p>
            <p>{errorMessage}</p>
          </div>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer flex-shrink-0"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
          )}
        </div>
      )}

      {/* Vertical SaaS Progress Steps */}
      <div className="space-y-4 max-w-sm mx-auto">
        {steps.map((st, idx) => {
          const state = getStepState(st.key, idx);
          return (
            <div key={st.key} className="flex items-center gap-3.5">
              <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                {state === 'done' ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                ) : state === 'active' ? (
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                ) : (
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-300" />
                )}
              </div>
              <span
                className={`text-sm ${
                  state === 'done'
                    ? 'text-slate-900 font-semibold'
                    : state === 'active'
                    ? 'text-blue-700 font-semibold'
                    : 'text-slate-400 font-normal'
                }`}
              >
                {st.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Document Progress Breakdown */}
      {uploadedDocs.length > 0 && stage !== 'Completed' && !errorMessage && (
        <div className="pt-4 border-t border-slate-100 space-y-2">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-center">
            Processing Files ({completedDocs.length} / {uploadedDocs.length})
          </p>
          <div className="space-y-1.5">
            {uploadedDocs.map((doc) => {
              const isDone = completedDocs.includes(doc.id);
              const isCurrent = currentDocName === doc.file.name;
              return (
                <div
                  key={doc.id}
                  className="flex items-center justify-between text-xs px-3 py-1.5 rounded bg-slate-50 border border-slate-100"
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                    <span className="truncate font-medium text-slate-700">{doc.file.name}</span>
                  </div>
                  <span className={`text-[10px] font-semibold ${isDone ? 'text-emerald-600' : isCurrent ? 'text-blue-600' : 'text-slate-400'}`}>
                    {isDone ? 'Done' : isCurrent ? 'Processing...' : 'Queued'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
