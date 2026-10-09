import React from 'react';
import { ArrowRight, ShieldCheck } from 'lucide-react';

export default function Header({ onGoHome, isLanding, onStart }) {
  return (
    <header className={`pv-header ${isLanding ? 'pv-header-landing' : ''}`}>
      <div className="pv-header-inner">
        {/* Left: Brand Logo & Title */}
        <div
          onClick={onGoHome}
          className="pv-brand"
        >
          <div className="pv-brand-icon">
            <ShieldCheck size={19} />
          </div>
          <div>
            <strong>PropVerify</strong>
            <p>
              Property Document Verification
            </p>
          </div>
        </div>

        {isLanding ? <><nav className="pv-nav" aria-label="Main navigation"><a href="#what-we-check">What We Check</a><a href="#how-it-works">How It Works</a><a href="#documentation">Documentation</a></nav><button className="pv-nav-cta" onClick={onStart}>Start Verification <ArrowRight size={15} /></button></> : <button className="pv-flow-home" onClick={onGoHome}>Back to home</button>}
      </div>
    </header>
  );
}


