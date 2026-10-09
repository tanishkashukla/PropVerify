import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Image as ImageIcon,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  ArrowLeft,
  Play
} from 'lucide-react';
import StepIndicator from './StepIndicator';
import { DOCUMENT_TYPES, documentTypeLabel } from '../constants/documentTypes';

const ALL_DOCUMENT_TYPES = DOCUMENT_TYPES;

const inferDocumentType = (filename) => {
  const name = filename.toUpperCase();
  if (name.includes('INDEX')) return 'index_ii';
  if (name.includes('7_12') || name.includes('712')) return '7_12_extract';
  if (name.includes('PROPERTY') || name.includes('CARD')) return 'property_card';
  if (name.includes('SALE') || name.includes('DEED')) return 'sale_deed';
  if (name.includes('ID') || name.includes('IDENTITY') || name.includes('PASSPORT') || name.includes('PROOF')) return 'id_document';
  return '';
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

export default function UploadDocuments({
  requiredDocuments = ALL_DOCUMENT_TYPES.map(({ id }) => id),
  onChange,
  onStartVerification,
  onBack,
  className = ''
}) {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const notifyParent = (filesList) => {
    if (onChange) {
      const payload = filesList.map((item) => ({
        file: item.file,
        documentType: item.documentType,
        id: item.id
      }));
      onChange(payload);
    }
  };

  const validateAndAddFiles = (files) => {
    setErrorMsg('');
    const newItems = [];
    const validExtensions = ['pdf', 'jpg', 'jpeg', 'png'];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.split('.').pop().toLowerCase();

      if (!validExtensions.includes(ext)) {
        setErrorMsg(`Unsupported file type: "${file.name}". Please upload PDF, JPG, or PNG files only.`);
        continue;
      }

      if (file.size === 0) {
        setErrorMsg(`File "${file.name}" is empty (0 bytes) and cannot be processed.`);
        continue;
      }

      if (file.size > 25 * 1024 * 1024) {
        setErrorMsg(`File "${file.name}" exceeds the 25 MB per-file limit.`);
        continue;
      }

      const exists = uploadedFiles.some((f) => f.file.name === file.name && f.file.size === file.size);
      if (exists) {
        continue;
      }

      const inferred = inferDocumentType(file.name);
      newItems.push({
        id: Math.random().toString(36).substring(2, 9),
        file,
        documentType: inferred,
        extension: ext.toUpperCase()
      });
    }

    if (newItems.length > 0) {
      const updated = [...uploadedFiles, ...newItems];
      setUploadedFiles(updated);
      notifyParent(updated);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndAddFiles(e.target.files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndAddFiles(e.dataTransfer.files);
    }
  };

  const handleDocumentTypeChange = (id, newType) => {
    const updated = uploadedFiles.map((item) => {
      if (item.id === id) {
        return { ...item, documentType: newType };
      }
      return item;
    });

    setUploadedFiles(updated);
    notifyParent(updated);
  };

  const handleRemoveFile = (id) => {
    const updated = uploadedFiles.filter((item) => item.id !== id);
    setUploadedFiles(updated);
    notifyParent(updated);
  };

  // Check missing required document types
  const uploadedTypes = uploadedFiles.map((item) => item.documentType).filter(Boolean);
  const missingRequiredTypes = requiredDocuments.filter((type) => !uploadedTypes.includes(type));

  const isStartDisabled = uploadedFiles.length === 0;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Step Indicator */}
      <StepIndicator currentStep={2} />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-blue-600" />
              Upload Documents
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Upload the selected property documents for verification.
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 bg-slate-100 text-slate-700 rounded-md font-semibold self-start sm:self-auto border border-slate-200">
            {uploadedFiles.length} file{uploadedFiles.length === 1 ? '' : 's'} uploaded
          </span>
        </div>

        {/* Large Subtle Dashed Border Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current && fileInputRef.current.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all select-none ${
            isDragging
              ? 'border-blue-500 bg-blue-50/50'
              : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50/50'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            className="hidden"
          />

          <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="text-sm font-bold text-slate-800">
            Drag &amp; drop documents here
          </p>
          <p className="text-xs font-semibold text-blue-600 mt-1">
            or Browse Files
          </p>
          <p className="text-[11px] text-slate-400 mt-2 font-medium">
            PDF, JPG or PNG &bull; Max 25 MB
          </p>
        </div>

        {/* Error Banner */}
        {errorMsg && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
            <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Compact Uploaded Documents List */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-3 pt-2">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Uploaded Documents ({uploadedFiles.length})
            </h3>

            <div className="space-y-2">
              {uploadedFiles.map((item) => (
                <div
                  key={item.id}
                  className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-center justify-between gap-4 text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="w-8 h-8 rounded bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-[10px] flex-shrink-0">
                      {item.extension}
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold text-slate-900 truncate">{item.file.name}</p>
                      <p className="text-[11px] text-slate-400">{formatFileSize(item.file.size)}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] font-semibold text-slate-500 hidden sm:inline">
                        Document Type:
                      </span>
                      <select
                        value={item.documentType}
                        onChange={(e) => handleDocumentTypeChange(item.id, e.target.value)}
                        className={`text-xs rounded-lg border px-2.5 py-1.5 bg-white font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          item.documentType
                            ? 'border-blue-300 text-blue-900 bg-blue-50/30'
                            : 'border-slate-300 text-slate-500'
                        }`}
                      >
                        <option value="">Select Document Type...</option>
                        {ALL_DOCUMENT_TYPES.map((type) => (
                          <option key={type.id} value={type.id}>
                            {type.label} {requiredDocuments.includes(type.id) ? '(Required)' : '(Optional)'}
                          </option>
                        ))}
                      </select>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleRemoveFile(item.id)}
                      className="text-xs text-red-600 hover:text-red-800 font-semibold px-2 py-1 rounded hover:bg-red-50 cursor-pointer transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Compact Document Checklist */}
        <div className="pt-2 space-y-3">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Document Checklist
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {requiredDocuments.map((docType) => {
              const isUploaded = uploadedFiles.some((item) => item.documentType === docType);
              const label = documentTypeLabel(docType);

              return (
                <div
                  key={docType}
                  className={`p-2.5 rounded-lg border text-xs font-medium flex items-center justify-between ${
                    isUploaded
                      ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
                      : 'bg-amber-50/70 border-amber-200 text-amber-950'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {isUploaded ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                    )}
                    <span className="font-semibold">{label}</span>
                  </div>
                  <span className="text-[10px] font-bold uppercase">
                    {isUploaded ? '✓ Uploaded' : 'Not Uploaded'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Missing Required Document Alert Banner */}
        {missingRequiredTypes.length > 0 && uploadedFiles.length > 0 && (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-1 text-xs text-amber-900">
            <div className="flex items-center gap-2 font-bold text-amber-950 text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-600" /> Missing Required Document
            </div>
            <p>
              <span className="font-bold">{missingRequiredTypes.map(documentTypeLabel).join(', ')}</span> {missingRequiredTypes.length === 1 ? 'has' : 'have'} been selected as required but {missingRequiredTypes.length === 1 ? 'has' : 'have'} not been uploaded.
            </p>
            <p>You can continue now; PropVerify will include these as missing in the verification results.</p>
          </div>
        )}

        {/* Bottom Bar: Action Buttons */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-4">
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
          )}

          <button
            type="button"
            onClick={onStartVerification}
            disabled={isStartDisabled}
            className={`px-6 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 shadow-sm transition-all ml-auto ${
              !isStartDisabled
                ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            <span>Start Verification</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
