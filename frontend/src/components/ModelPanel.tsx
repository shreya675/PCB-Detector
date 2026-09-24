import type { ModelInfo, MetricPoint } from "../types";
import { Icon } from "./Icon";
import { MetricCard } from "./MetricCard";
import { StatusBadge } from "./StatusBadge";

const MODEL_CLASSES = [
  "open_circuit", "short_circuit", "spur", "spurious_copper", "mouse_bite", "missing_hole", "pin_hole",
];

interface ModelPanelProps {
  info: ModelInfo | null;
  apiVersion?: string;
}

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

function MetricRow({ label, point }: { label: string; point: MetricPoint }) {
  return (
    <tr>
      <td>{label}</td>
      <td>{pct(point.precision)}</td>
      <td>{pct(point.recall)}</td>
      <td>{point.tp ?? "—"}</td>
      <td>{point.fp ?? "—"}</td>
      <td>{point.fn ?? "—"}</td>
    </tr>
  );
}

export function ModelPanel({ info, apiVersion }: ModelPanelProps) {
  const available = info?.model_status === "available";
  const card = info?.evaluation ?? null;
  const op = card?.evaluation.operating_point;
  const val = card?.evaluation.ultralytics_val;

  return (
    <div className="stack">
      <section className="panel model-panel">
        <div className="model-head">
          <div className="model-icon"><Icon name="model" /></div>
          <div>
            <h2>{card ? card.name : available ? "Detection model loaded" : "No evaluated project model available"}</h2>
            <span className="muted" style={{ fontSize: 13 }}>{card?.architecture ?? "Ultralytics YOLO object detector"}</span>
          </div>
        </div>
        <p>
          {card
            ? `Trained on ${card.dataset.name} (${card.dataset.split}; ${card.dataset.train} train / ${card.dataset.val} val / ${card.dataset.test} test images at ${card.dataset.image_size} px). All numbers below come from the held-out ${card.evaluation.split}.`
            : available
              ? "A weights file is configured on the server, but no evaluation record matches it. Run the evaluation and update the model card before interpreting results."
              : "Train and evaluate the baseline, then place the weights at the configured model path to enable inspections."}
        </p>

        <div className="model-facts">
          <div><span>Model status</span><strong>{info ? <StatusBadge value={info.model_status} /> : "Unknown"}</strong></div>
          <div><span>Weights</span><strong>{info?.weights_file ?? "—"}</strong></div>
          <div><span>Checksum</span><strong>{info?.model_version ?? "—"}</strong></div>
          <div><span>Confidence threshold</span><strong>{info ? info.confidence_threshold : "—"}</strong></div>
          <div><span>Post-processing</span><strong>{info ? (info.postprocess.enabled ? `NMS ${info.postprocess.nms_iou} · box ×${info.postprocess.box_scale}` : "off") : "—"}</strong></div>
          <div><span>API version</span><strong>{apiVersion ?? "Unavailable"}</strong></div>
          <div><span>Certification</span><strong>None · research only</strong></div>
        </div>

        {info?.evaluation_mismatch && (
          <div className="error-banner" role="alert">
            The model card on the server was written for different weights than the ones loaded, so its metrics are hidden.
          </div>
        )}
      </section>

      {card && op && val && (
        <>
          <div className="metrics-grid">
            <MetricCard label="Precision" value={pct(op.with_postprocess.precision)} note={`Operating point conf ${op.conf}, IoU ${op.match_iou}, with post-processing`} tone="green" />
            <MetricCard label="Recall" value={pct(op.with_postprocess.recall)} note={`${op.with_postprocess.fn ?? "—"} of ${(op.with_postprocess.tp ?? 0) + (op.with_postprocess.fn ?? 0)} labelled defects missed`} tone="green" />
            <MetricCard label="mAP@0.5" value={pct(val.mAP50)} note={`Ultralytics val, conf ${val.conf}`} />
            <MetricCard label="mAP@0.5:0.95" value={pct(val.mAP50_95)} note="Localisation quality across IoU thresholds" />
          </div>

          <section className="panel">
            <div className="panel-heading">
              <h2>Held-out test results</h2>
              <span>{card.evaluation.split}</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr><th>Setting</th><th>Precision</th><th>Recall</th><th>TP</th><th>FP</th><th>FN</th></tr>
                </thead>
                <tbody>
                  <MetricRow label={`Model only (conf ${op.conf}, IoU ${op.match_iou})`} point={op.model_only} />
                  <MetricRow label="Model + post-processing (what the API runs)" point={op.with_postprocess} />
                  <MetricRow label="Defect-level (any class)" point={op.defect_level_with_postprocess} />
                  <MetricRow label={`Ultralytics val (conf ${val.conf}, IoU ${val.iou})`} point={{ precision: val.precision, recall: val.recall }} />
                  {card.evaluation.reference && (
                    <MetricRow label={`Reference: ${card.evaluation.reference.paper}`} point={{ precision: card.evaluation.reference.precision, recall: card.evaluation.reference.recall }} />
                  )}
                </tbody>
              </table>
            </div>
            {op.note && <p className="muted" style={{ fontSize: 13, marginTop: 10 }}>{op.note}. Defect-level counts a detection as correct when it overlaps a labelled defect regardless of class.</p>}
          </section>

          <section className="panel">
            <div className="panel-heading"><h2>Per-class results (with post-processing)</h2></div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr><th>Class</th><th>Precision</th><th>Recall</th><th>TP</th><th>FP</th><th>FN</th></tr>
                </thead>
                <tbody>
                  {Object.entries(card.evaluation.per_class_with_postprocess).map(([name, point]) => (
                    <MetricRow key={name} label={name} point={point} />
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {card.known_limitations && card.known_limitations.length > 0 && (
            <section className="panel">
              <div className="panel-heading"><h2>Known limitations</h2></div>
              <ul className="plain-list">
                {card.known_limitations.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </section>
          )}
        </>
      )}

      <section className="panel">
        <h2 style={{ fontSize: 15 }}>Declared output classes</h2>
        <div className="class-list">
          {MODEL_CLASSES.map((name) => (
            <span className={card?.dataset.untrained_classes?.includes(name) ? "class-chip class-chip-muted" : "class-chip"} key={name}>
              {name}{card?.dataset.untrained_classes?.includes(name) ? " (no training data)" : ""}
            </span>
          ))}
        </div>
        {!card && (
          <div className="info-banner" style={{ marginTop: 14 }}>
            Accuracy metrics are shown only from a reproducible held-out evaluation run that matches the loaded weights. No placeholder numbers are displayed.
          </div>
        )}
      </section>
    </div>
  );
}
