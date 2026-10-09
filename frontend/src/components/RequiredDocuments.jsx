import React from 'react';
import { FileText, CheckSquare, Square, ArrowRight, ArrowLeft } from 'lucide-react';
import StepIndicator from './StepIndicator';
import { DOCUMENT_TYPES } from '../constants/documentTypes';

const DEFAULT_DOCUMENTS = [
  { ...DOCUMENT_TYPES[0], description: 'Primary legal ownership transfer document' },
  { ...DOCUMENT_TYPES[1], description: 'Urban property registry record' },
  { ...DOCUMENT_TYPES[2], description: 'Registration summary document' },
  { ...DOCUMENT_TYPES[3], description: 'Land/revenue record' },
  { ...DOCUMENT_TYPES[4], description: 'Government identity proof' },
];

export default function RequiredDocuments({ selectedDocuments = DEFAULT_DOCUMENTS.map((doc) => doc.id), onChange, onNext, onBack, className = '' }) {
  const selectedDocs = selectedDocuments;

  const toggleDocument = (docName) => {
    const updated = selectedDocs.includes(docName)
      ? selectedDocs.filter((id) => id !== docName)
      : [...selectedDocs, docName];

    if (onChange) {
      onChange(updated);
    }
  };

  const selectAll = () => {
    const all = DEFAULT_DOCUMENTS.map((doc) => doc.id);
    if (onChange) {
      onChange(all);
    }
  };

  const deselectAll = () => {
    if (onChange) {
      onChange([]);
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Step Indicator */}
      <StepIndicator currentStep={1} />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              Required Documents
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Select the documents that are required for this property verification. You can customize the required document set depending on the property case.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium self-start sm:self-auto">
            <button
              type="button"
              onClick={selectAll}
              className="text-blue-600 hover:text-blue-800 transition-colors px-2 py-1 rounded hover:bg-blue-50 cursor-pointer"
            >
              Select All
            </button>
            <span className="text-slate-300">|</span>
            <button
              type="button"
              onClick={deselectAll}
              className="text-slate-500 hover:text-slate-700 transition-colors px-2 py-1 rounded hover:bg-slate-100 cursor-pointer"
            >
              Deselect All
            </button>
          </div>
        </div>

        {/* Clean Horizontal Checklist Rows */}
        <div className="space-y-3">
          {DEFAULT_DOCUMENTS.map((doc) => {
            const isSelected = selectedDocs.includes(doc.id);
            return (
              <div
                key={doc.id}
                onClick={() => toggleDocument(doc.id)}
                className={`flex items-center justify-between p-4 rounded-lg border transition-all cursor-pointer select-none ${
                  isSelected
                    ? 'bg-blue-50/50 border-blue-200 text-slate-900 shadow-2xs'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center gap-3.5">
                  <div className="pt-0.5">
                    {isSelected ? (
                      <CheckSquare className="w-5 h-5 text-blue-600 fill-blue-50" />
                    ) : (
                      <Square className="w-5 h-5 text-slate-400" />
                    )}
                  </div>
                  <div>
                    <span className={`text-sm font-semibold ${isSelected ? 'text-slate-900' : 'text-slate-700'}`}>
                      {doc.label}
                    </span>
                    <p className="text-xs text-slate-400 mt-0.5">{doc.description}</p>
                  </div>
                </div>

                <span
                  className={`text-[11px] px-2.5 py-0.5 rounded-full font-semibold ${
                    isSelected
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {isSelected ? 'Required' : 'Optional'}
                </span>
              </div>
            );
          })}
        </div>

        {/* Bottom Bar: Selection Counter & Navigation Buttons */}
        <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-xs font-semibold text-slate-500">
            Selected: {selectedDocs.length} of {DEFAULT_DOCUMENTS.length} documents
          </span>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                className="px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition-colors w-full sm:w-auto"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
            )}

            <button
              type="button"
              onClick={onNext}
              disabled={selectedDocs.length === 0}
              className={`px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-all w-full sm:w-auto ${
                selectedDocs.length > 0
                  ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed'
              }`}
            >
              <span>Continue to Upload Documents</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
