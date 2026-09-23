import { useState } from "react";
import { api } from "../lib/api";
import { formatDate } from "../lib/analytics";
import type { Inspection } from "../types";
import { DefectTable } from "./DefectTable";
import { StatusBadge } from "./StatusBadge";

type ImageKind = "annotated" | "test" | "reference";

interface InspectionResultProps {
  inspection: Inspection;
  onBack: () => void;
}

export function InspectionResult({ inspection, onBack }: InspectionResultProps) {
  const [kind, setKind] = useState<ImageKind>("annotated");
  const counts = inspection.summary.severity_counts || {};
  const hasReference = Boolean(inspection.reference_image_path);
  const quality = inspection.alignment_quality;

  const tabs: { id: ImageKind; label: string }[] = [
    { id: "annotated", label: "Annotated" },
    { id: "test", label: "Original" },
    ...(hasReference ? [{ id: "reference" as const, label: "Reference" }] : []),
  ];

  return (
    <div className="stack">
      <button className="text-button back-button" onClick={onBack}>← Back to inspections</button>

      <section className="result-hero panel">
        <div>
          <h1>Inspection #{inspection.id.slice(0, 8)}</h1>
          <p>
            {formatDate(inspection.created_at)} · Model <span className="mono">{inspection.model_version}</span>
          </p>
        </div>
        <StatusBadge value={inspection.status} large />
      </section>

      {inspection.summary.coverage_warning && (
        <div className="info-banner" role="status">{inspection.summary.coverage_warning}</div>
      )}

      <div className="result-grid">
        <section className="panel image-panel">
          <div className="panel-heading">
            <h2>Board image</h2>
            <div className="image-tabs">
              {tabs.map((tab) => (
                <button key={tab.id} className={kind === tab.id ? "active" : ""} onClick={() => setKind(tab.id)}>
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
          <div className="inspection-image">
            <img src={api.imageUrl(inspection.id, kind)} alt={`${kind} PCB image`} />
          </div>
        </section>

        <aside className="panel evidence-panel">
          <h2>Summary</h2>
          <div className="evidence-count">
            <strong>{inspection.summary.defect_count || 0}</strong>
            <span>findings</span>
          </div>
          <dl className="kv-list">
            <div><dt>Critical</dt><dd>{counts.critical || 0}</dd></div>
            <div><dt>Major</dt><dd>{counts.major || 0}</dd></div>
            <div><dt>Minor</dt><dd>{counts.minor || 0}</dd></div>
            <div><dt>Reference comparison</dt><dd>{inspection.summary.reference_comparison ? "Yes" : "No"}</dd></div>
            {inspection.summary.heuristic_count !== undefined && (
              <div><dt>Heuristic findings</dt><dd>{inspection.summary.heuristic_count}</dd></div>
            )}
          </dl>
          {quality && (
            <div className="quality-note">
              <strong>Registration passed</strong>
              Inlier ratio {Math.round(Number(quality.inlier_ratio || 0) * 100)}% · overlap {Math.round(Number(quality.overlap_ratio || 0) * 100)}%
            </div>
          )}
          <a className="primary-button report-button" href={api.reportUrl(inspection.id)}>Download PDF report</a>
        </aside>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <h2>Defect log</h2>
          <span>{inspection.defects.length} entries</span>
        </div>
        <DefectTable defects={inspection.defects} />
      </section>
    </div>
  );
}
