import React from 'react';
import { ChevronRight } from 'lucide-react';

export default function StepIndicator({ currentStep = 1 }) {
  const steps = [
    { number: 1, label: 'Required Documents' },
    { number: 2, label: 'Upload Documents' },
    { number: 3, label: 'Verification' }
  ];

  return (
    <div className="flex items-center justify-center gap-2 text-xs font-medium py-3 px-4 bg-white rounded-lg border border-slate-200 shadow-sm max-w-xl mx-auto mb-6">
      {steps.map((step, idx) => {
        const isCurrent = currentStep === step.number;
        const isCompleted = currentStep > step.number;

        return (
          <React.Fragment key={step.number}>
            <div className={`flex items-center gap-1.5 ${
              isCurrent
                ? 'text-blue-600 font-bold'
                : isCompleted
                ? 'text-emerald-700 font-semibold'
                : 'text-slate-400'
            }`}>
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] ${
                isCurrent
                  ? 'bg-blue-600 text-white'
                  : isCompleted
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-100 text-slate-500 border border-slate-300'
              }`}>
                {isCompleted ? '✓' : step.number}
              </span>
              <span>{step.label}</span>
            </div>

            {idx < steps.length - 1 && (
              <ChevronRight className="w-3.5 h-3.5 text-slate-300 mx-1" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
