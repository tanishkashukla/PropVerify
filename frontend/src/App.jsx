import React, { useState } from 'react';
import Header from './components/Header';
import LandingPage from './components/LandingPage';
import RequiredDocuments from './components/RequiredDocuments';
import UploadDocuments from './components/UploadDocuments';
import ProcessingStatus from './components/ProcessingStatus';
import VerificationDashboard from './components/VerificationDashboard';
import ComparisonView from './components/ComparisonView';
import StepIndicator from './components/StepIndicator';
import { verifyDocuments } from './services/api';

export default function App() {
  // Navigation step state: 0=Landing, 1=Required, 2=Upload, 3=Processing, 4=Dashboard, 5=Comparison
  const [currentStep, setCurrentStep] = useState(0);

  const [requiredDocs, setRequiredDocs] = useState([
    'sale_deed',
    'property_card',
    'index_ii',
    '7_12_extract',
    'id_document'
  ]);

  const [uploadedDocs, setUploadedDocs] = useState([]);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState('Uploading');
  const [completedDocIds, setCompletedDocIds] = useState([]);
  const [currentDocName, setCurrentDocName] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Verification result state
  const [verificationResult, setVerificationResult] = useState(null);
  const [activeMismatch, setActiveMismatch] = useState(null);

  const handleStartVerification = async () => {
    if (uploadedDocs.length === 0) {
      setErrorMessage('Upload at least one document before starting verification.');
      setCurrentStep(3);
      return;
    }
    setCurrentStep(3);
    setIsProcessing(true);
    setErrorMessage('');
    setVerificationResult(null);
    setActiveMismatch(null);
    setCompletedDocIds([]);

    try {
      setProcessingStage('Extracting');
      setCurrentDocName('');

      const result = await verifyDocuments(uploadedDocs, requiredDocs);

      setCompletedDocIds(uploadedDocs.map((item) => item.id));
      setProcessingStage('Completed');
      setVerificationResult(result);
      setCurrentStep(4);
    } catch (err) {
      console.error('Verification flow error:', err);
      setErrorMessage(err.message || 'Verification process failed. Please ensure backend is running on http://127.0.0.1:8001.');
      setProcessingStage('Error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setVerificationResult(null);
    setActiveMismatch(null);
    setIsProcessing(false);
    setErrorMessage('');
    setProcessingStage('Uploading');
    setCompletedDocIds([]);
    setCurrentDocName('');
    setUploadedDocs([]);
    setCurrentStep(0);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900 antialiased">
      {/* SaaS App Header */}
      <Header
        onGoHome={() => setCurrentStep(0)}
        isLanding={currentStep === 0}
        onStart={() => setCurrentStep(1)}
      />

      {/* Main Content Body */}
      <main className={currentStep === 0 ? 'pv-main-home' : `flex-1 w-full mx-auto px-4 sm:px-8 py-6 flex flex-col max-w-5xl`}>
        {/* PAGE 1: Landing Page */}
        {currentStep === 0 && (
          <LandingPage onStart={() => setCurrentStep(1)} />
        )}

        {/* PAGE 2: Select Required Documents */}
        {currentStep === 1 && (
          <RequiredDocuments
            selectedDocuments={requiredDocs}
            onChange={(docs) => setRequiredDocs(docs)}
            onNext={() => setCurrentStep(2)}
            onBack={() => setCurrentStep(0)}
          />
        )}

        {/* PAGE 3: Upload Documents */}
        {currentStep === 2 && (
          <UploadDocuments
            requiredDocuments={requiredDocs}
            onChange={(filesList) => setUploadedDocs(filesList)}
            onStartVerification={handleStartVerification}
            onBack={() => setCurrentStep(1)}
          />
        )}

        {/* PAGE 4: Processing State */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <StepIndicator currentStep={3} />
            <ProcessingStatus
              stage={processingStage}
              uploadedDocs={uploadedDocs}
              completedDocs={completedDocIds}
              currentDocName={currentDocName}
              errorMessage={errorMessage}
              onRetry={handleStartVerification}
            />
          </div>
        )}

        {/* PAGE 5: Verification Dashboard */}
        {currentStep === 4 && verificationResult && (
          <div className="space-y-6">
            <StepIndicator currentStep={3} />
            <VerificationDashboard
              result={verificationResult}
              onReset={handleReset}
              onSelectMismatch={(mismatch) => {
                setActiveMismatch(mismatch);
                setCurrentStep(5);
              }}
            />
          </div>
        )}

        {/* PAGE 6: Detailed Mismatch / Issues Comparison View */}
        {currentStep === 5 && verificationResult && (
          <div className="space-y-6">
            <StepIndicator currentStep={3} />
            <ComparisonView
              result={verificationResult}
              selectedIssue={activeMismatch}
              onBack={() => {
                setActiveMismatch(null);
                setCurrentStep(4);
              }}
            />
          </div>
        )}
      </main>

      {/* App Simple Footer */}
      {currentStep !== 0 && <footer className="bg-white border-t border-slate-200 py-5 text-center text-xs text-slate-400">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-8">
          <p>PropVerify &copy; 2026. Property Document Verification.</p>
        </div>
      </footer>}
    </div>
  );
}

