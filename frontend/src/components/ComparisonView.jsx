import React, { useEffect, useState } from 'react';
import { documentTypeLabel } from '../constants/documentTypes';
import {
  ArrowLeft,
  AlertTriangle,
  FileText,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  ListFilter
} from 'lucide-react';

export default function ComparisonView({
  result,
  selectedIssue = null,
  onBack,
  className = ''
}) {
  if (!result) return null;

  const mismatches = result.mismatches || [];
  const missingDocs = result.missing_documents || [];

  // Combine issues: field mismatches + missing documents
  const allIssues = [
    ...mismatches.map((m) => ({ type: 'mismatch', id: m.field, data: m })),
    ...missingDocs.map((md) => ({ type: 'missing_doc', id: md.expected_document_type, data: md }))
  ];

  // Selected issue state
  const initialIndex = selectedIssue
    ? allIssues.findIndex((iss) => iss.id === (selectedIssue.field || selectedIssue.expected_document_type))
    : 0;

  const [activeIssueIndex, setActiveIssueIndex] = useState(initialIndex >= 0 ? initialIndex : 0);

  useEffect(() => {
    const nextIndex = selectedIssue
      ? allIssues.findIndex((issue) => issue.id === (selectedIssue.field || selectedIssue.expected_document_type))
      : 0;
    setActiveIssueIndex(nextIndex >= 0 ? nextIndex : 0);
  }, [result, selectedIssue]);

  const activeIssue = allIssues[activeIssueIndex] || allIssues[0];

  if (!activeIssue) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center space-y-4">
        <CheckCircle2 className="w-12 h-12 text-emerald-600 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900">No Discrepancies Found</h2>
        <p className="text-xs text-slate-500">All evaluated fields and required documents passed verification.</p>
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const isMismatch = activeIssue.type === 'mismatch';
  const issueData = activeIssue.data;

  // Determine majority value for mismatch comparison
  let valuesMap = {};
  let majorityVal = '';
  if (isMismatch && issueData.values) {
    valuesMap = issueData.values;
    const counts = {};
    Object.values(valuesMap).forEach((v) => {
      counts[v] = (counts[v] || 0) + 1;
    });
    let maxCount = 0;
    Object.entries(counts).forEach(([val, cnt]) => {
      if (cnt > maxCount) {
        maxCount = cnt;
        majorityVal = val;
      }
    });
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Navigation Bar */}
      <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <button
          type="button"
          onClick={onBack}
          className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">
            Issue {activeIssueIndex + 1} of {allIssues.length}
          </span>
        </div>
      </div>

      {/* Main Grid: Issue Sidebar + Detailed Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Issue Selector Sidebar */}
        {allIssues.length > 1 && (
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3 md:col-span-1">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <ListFilter className="w-4 h-4 text-blue-600" /> Discrepancies List ({allIssues.length})
            </h3>

            <div className="space-y-2">
              {allIssues.map((issue, idx) => {
                const isActive = idx === activeIssueIndex;
                const isFieldMismatch = issue.type === 'mismatch';
                const label = isFieldMismatch
                  ? issue.data.field.replace(/_/g, ' ')
                  : `${documentTypeLabel(issue.data.expected_document_type)} (Missing)`;

                return (
                  <div
                    key={idx}
                    onClick={() => setActiveIssueIndex(idx)}
                    className={`p-3 rounded-lg border text-xs cursor-pointer transition-all flex items-center justify-between ${
                      isActive
                        ? 'bg-blue-50 border-blue-300 text-blue-900 font-semibold shadow-sm'
                        : 'bg-slate-50/50 border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <AlertTriangle className={`w-4 h-4 flex-shrink-0 ${isFieldMismatch ? 'text-red-500' : 'text-amber-500'}`} />
                      <span className="capitalize truncate">{label}</span>
                    </div>
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                      {issue.data.severity}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Detailed Comparison Panel */}
        <div className={`space-y-6 ${allIssues.length > 1 ? 'md:col-span-2' : 'md:col-span-3'}`}>
          {isMismatch ? (
            /* Field Mismatch Detail Card */
            <div className="bg-white rounded-xl border border-red-200 shadow-sm p-6 space-y-6">
              {/* Issue Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-red-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 bg-red-100 text-red-800 font-bold rounded-md text-[10px] uppercase">
                      ⚠ MISMATCH
                    </span>
                    <span className="px-2.5 py-0.5 bg-red-100 text-red-800 font-bold rounded-md text-[10px] uppercase">
                      Severity: {issueData.severity}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 capitalize mt-2">
                    {issueData.field.replace(/_/g, ' ')}
                  </h2>
                </div>
              </div>

              {/* Comparison Table */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-blue-600" /> Extracted Values Per Document
                </h3>

                <div className="overflow-x-auto border border-slate-200 rounded-xl">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200">
                        <th className="py-3 px-4">Document</th>
                        <th className="py-3 px-4">Extracted Value</th>
                        <th className="py-3 px-4 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {Object.entries(valuesMap).map(([file, val]) => {
                        const conflictingDocuments = issueData.conflicting_documents || [];
                        const isConflict = conflictingDocuments.length > 0
                          ? conflictingDocuments.includes(file)
                          : val !== majorityVal;
                        // Infer readable document label from filename
                        let docLabel = file;
                        if (file.includes('Sale_Deed')) docLabel = 'Sale Deed';
                        else if (file.includes('Property_Card')) docLabel = 'Property Card';
                        else if (file.includes('Index_II')) docLabel = 'Index II';
                        else if (file.includes('7_12')) docLabel = '7/12 Extract';
                        else if (file.includes('ID_Document')) docLabel = 'ID Document';

                        return (
                          <tr
                            key={file}
                            className={`transition-colors ${
                              isConflict ? 'bg-red-50/70 font-semibold text-red-950' : 'hover:bg-slate-50'
                            }`}
                          >
                            <td className="py-3 px-4 font-medium text-slate-900">
                              <div>{docLabel}</div>
                              <div className="text-[10px] text-slate-400 font-normal">{file}</div>
                            </td>
                            <td className="py-3 px-4 font-mono font-bold text-slate-900">
                              <span className={isConflict ? 'text-red-700 bg-red-100 px-2 py-0.5 rounded' : ''}>
                                {val}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              {isConflict ? (
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-red-100 text-red-700 font-bold text-xs" title="Conflicting Value">
                                  ⚠
                                </span>
                              ) : (
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 font-bold text-xs" title="Matches Majority">
                                  ✓
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Issue Explanation */}
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl space-y-1 text-xs">
                <p className="font-semibold text-red-900 text-sm">Issue Explanation</p>
                <p className="text-red-800">{issueData.message}</p>
              </div>
            </div>
          ) : (
            /* Missing Document Detail Card */
            <div className="bg-white rounded-xl border border-amber-200 shadow-sm p-6 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-amber-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 bg-amber-200 text-amber-900 font-bold rounded-md text-[10px] uppercase">
                      ⚠ NOT PROVIDED
                    </span>
                    <span className="px-2.5 py-0.5 bg-amber-200 text-amber-900 font-bold rounded-md text-[10px] uppercase">
                      Severity: {issueData.severity}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-amber-950 mt-2">
                    Missing Document: {documentTypeLabel(issueData.expected_document_type)}
                  </h2>
                </div>
              </div>

              <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-2 text-xs text-amber-900">
                <p className="font-semibold text-sm text-amber-950">Issue Summary</p>
                <p>{issueData.message}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
