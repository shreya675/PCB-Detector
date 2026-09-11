import { api } from "../lib/api";
import { formatDate } from "../lib/analytics";
import type { Inspection } from "../types";
import { DefectTable } from "./DefectTable";
import { StatusBadge } from "./StatusBadge";

export function InspectionResult({ inspection, onBack }: { inspection: Inspection; onBack: () => void }) {
  const counts = inspection.summary.severity_counts || {};
  return <div className="stack">
    <button className="text-button back-button" onClick={onBack}>← Back to inspections</button>
    <section className="result-hero panel"><div><span className="eyebrow">INSPECTION #{inspection.id.slice(0, 8)}</span><h1>Inspection result</h1><p>{formatDate(inspection.created_at)} · Model <span className="mono">{inspection.model_version}</span></p></div><StatusBadge value={inspection.status}/></section>
    {inspection.summary.coverage_warning && <div className="info-banner" role="status">{inspection.summary.coverage_warning}</div>}
    <div className="result-grid">
      <section className="panel image-panel"><div className="panel-heading"><div><span className="eyebrow">ANNOTATED OUTPUT</span><h2>Detected findings</h2></div></div><div className="inspection-image"><img src={api.imageUrl(inspection.id, "annotated")} alt="Annotated PCB with detected findings"/></div></section>
      <aside className="panel evidence-panel"><span className="eyebrow">SUMMARY</span><div className="evidence-count"><strong>{inspection.summary.defect_count || 0}</strong><span>total findings</span></div><dl><div><dt>Critical</dt><dd>{counts.critical || 0}</dd></div><div><dt>Major</dt><dd>{counts.major || 0}</dd></div><div><dt>Minor</dt><dd>{counts.minor || 0}</dd></div><div><dt>Reference used</dt><dd>{inspection.summary.reference_comparison ? "Yes" : "No"}</dd></div></dl>{inspection.alignment_quality && <div className="quality-note"><strong>Registration passed</strong><span>Inlier ratio {Math.round(Number(inspection.alignment_quality.inlier_ratio || 0) * 100)}% · overlap {Math.round(Number(inspection.alignment_quality.overlap_ratio || 0) * 100)}%</span></div>}<a className="primary-button report-button" href={api.reportUrl(inspection.id)}>Download PDF report</a></aside>
    </div>
    <section className="panel"><div className="panel-heading"><div><span className="eyebrow">DEFECT LOG</span><h2>Inspection findings</h2></div></div><DefectTable defects={inspection.defects}/></section>
  </div>;
}
