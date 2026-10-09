import React from 'react';
import {
  ArrowDown, ArrowRight, BadgeCheck, Building2, FileCheck2, FileSearch,
  FileText, Files, Fingerprint, GitCompareArrows, ScanText, ShieldCheck,
  TriangleAlert,
} from 'lucide-react';

const checks = [
  { icon: ScanText, title: 'Document Extraction', text: 'Extract important property information from uploaded documents.' },
  { icon: GitCompareArrows, title: 'Cross-Document Verification', text: 'Compare key property details across multiple documents.' },
  { icon: TriangleAlert, title: 'Mismatch Detection', text: 'Identify conflicting information and highlight discrepancies.' },
  { icon: FileCheck2, title: 'Verification Report', text: 'Generate a structured report summarizing verification results and issues.' },
];
const steps = [
  { icon: Files, title: 'Upload', text: 'Add the property records you have.' },
  { icon: ScanText, title: 'Extract', text: 'Key information is organized.' },
  { icon: GitCompareArrows, title: 'Compare', text: 'Details are checked across records.' },
  { icon: FileSearch, title: 'Detect issues', text: 'Inconsistencies are brought forward.' },
  { icon: FileCheck2, title: 'Get your report', text: 'Review a clear verification summary.' },
];
const documents = [
  { name: 'Sale Deed', icon: FileText }, { name: 'Property Card', icon: Building2 },
  { name: 'Index II', icon: Files }, { name: '7/12 Extract', icon: FileSearch },
  { name: 'ID Document', icon: Fingerprint },
];

function SectionHeading({ eyebrow, title, children }) {
  return <div className="pv-section-heading"><span className="pv-eyebrow">{eyebrow}</span><h2>{title}</h2>{children && <p>{children}</p>}</div>;
}

export default function LandingPage({ onStart }) {
  return (
    <div className="pv-home">
      <section className="pv-hero" id="top">
        <div className="pv-hero-copy">
          <div className="pv-kicker"><span className="pv-kicker-mark"><ShieldCheck size={15} /></span> Clarity across property records</div>
          <h1>PropVerify</h1>
          <p className="pv-hero-subtitle">Property Document Verification</p>
          <p className="pv-hero-text">Verify property documents, identify inconsistencies, detect missing records, and generate a detailed verification report.</p>
          <div className="pv-hero-actions">
            <button className="pv-button pv-button-primary" onClick={onStart}>Start Verification <ArrowRight size={17} /></button>
            <a className="pv-button pv-button-quiet" href="#how-it-works">How It Works <ArrowDown size={15} /></a>
          </div>
          <div className="pv-hero-note"><BadgeCheck size={17} /> A clear process for reviewing important property records</div>
        </div>
        <div className="pv-hero-visual" role="img" aria-label="Property documents being carefully reviewed on a desk">
          <div className="pv-hero-image" />
          <div className="pv-image-shade" />
          <div className="pv-photo-caption"><span className="pv-caption-rule" /><span>Property records, brought into focus</span></div>
          <div className="pv-document-float">
            <div className="pv-float-icon"><FileCheck2 size={19} /></div>
            <div><strong>Document review</strong><span>One organized verification process</span></div>
            <ArrowRight className="pv-float-arrow" size={16} />
          </div>
          <div className="pv-image-index">01 <span /> 04</div>
        </div>
        <div className="pv-hero-bottom"><span>PROPERTY DOCUMENT VERIFICATION</span><span>BUILT FOR A CLEARER REVIEW</span></div>
      </section>

      <section className="pv-section pv-checks" id="what-we-check">
        <SectionHeading eyebrow="A clearer picture, record by record" title="What PropVerify Checks">PropVerify analyzes property documents and checks important information across records to identify inconsistencies and missing details.</SectionHeading>
        <div className="pv-check-grid">{checks.map(({ icon: Icon, title, text }, i) => <article className="pv-check-card" key={title}><div className="pv-card-top"><span className="pv-icon-box"><Icon size={20} strokeWidth={1.7} /></span><span className="pv-card-index">0{i + 1}</span></div><h3>{title}</h3><p>{text}</p><div className="pv-card-line" /></article>)}</div>
      </section>

      <section className="pv-work-section" id="how-it-works">
        <div className="pv-section pv-work-inner">
          <SectionHeading eyebrow="A straightforward process" title="How It Works">From document upload to a detailed verification report, PropVerify simplifies the property document checking process.</SectionHeading>
          <div className="pv-steps">{steps.map(({ icon: Icon, title, text }, i) => <article className="pv-step" key={title}><div className="pv-step-top"><span className="pv-step-number">0{i + 1}</span><span className="pv-step-icon"><Icon size={19} strokeWidth={1.7} /></span></div><h3>{title}</h3><p>{text}</p>{i < steps.length - 1 && <span className="pv-step-connector" />}</article>)}</div>
        </div>
      </section>

      <section className="pv-section pv-documents" id="documentation">
        <SectionHeading eyebrow="Records in your review" title="Documents We Verify">Bring the key documents together for a more organized review.</SectionHeading>
        <div className="pv-doc-grid">{documents.map(({ name, icon: Icon }, i) => <article className="pv-doc-card" key={name}><div className="pv-doc-art"><span className="pv-doc-fold" /><Icon size={25} strokeWidth={1.5} /><span className="pv-doc-lines"><i /><i /><i /></span></div><div className="pv-doc-label"><span>{name}</span><span className="pv-doc-count">0{i + 1}</span></div></article>)}</div>
      </section>

      <footer className="pv-footer"><a className="pv-footer-brand" href="#top"><span><ShieldCheck size={19} /></span><span><strong>PropVerify</strong><small>Property Document Verification</small></span></a><span className="pv-footer-copy">© 2026 PropVerify</span><a className="pv-back-top" href="#top">Back to top ↑</a></footer>
    </div>
  );
}
