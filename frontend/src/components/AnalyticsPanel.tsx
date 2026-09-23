import { summarizeInspections } from "../lib/analytics";
import type { InspectionSummary } from "../types";

type Tone = "green" | "orange" | "red" | "blue";

function BarList({ rows, label }: { rows: readonly (readonly [string, number, Tone])[]; label: string }) {
  const max = Math.max(1, ...rows.map((row) => row[1]));
  return (
    <div className="bar-list" role="img" aria-label={label}>
      {rows.map(([name, value, tone]) => (
        <div className="bar-row" key={name}>
          <div className="bar-meta"><span>{name}</span><strong>{value}</strong></div>
          <div className="bar-track">
            <span className={`bar-fill fill-${tone}`} style={{ width: `${(value / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function AnalyticsPanel({ items }: { items: InspectionSummary[] }) {
  const data = summarizeInspections(items);

  const statusRows = [
    ["Pass", data.status.pass, "green"],
    ["Pass with warning", data.status.warning, "orange"],
    ["Fail", data.status.fail, "red"],
  ] as const;

  const severityRows = [
    ["Critical", data.severity.critical, "red"],
    ["Major", data.severity.major, "orange"],
    ["Minor", data.severity.minor, "blue"],
  ] as const;

  const withReference = items.filter((item) => item.summary.reference_comparison).length;
  const average = items.length ? (data.defects / items.length).toFixed(1) : "—";

  return (
    <div className="stack">
      <div className="analytics-grid">
        <section className="panel">
          <div className="panel-heading">
            <h2>Inspection outcomes</h2>
            <span>{items.length} records</span>
          </div>
          <BarList rows={statusRows} label={`Pass ${data.status.pass}, warning ${data.status.warning}, fail ${data.status.fail}`} />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Findings by severity</h2>
            <span>{data.defects} total</span>
          </div>
          <BarList rows={severityRows} label={`Critical ${data.severity.critical}, major ${data.severity.major}, minor ${data.severity.minor}`} />
        </section>
      </div>

      <section className="panel">
        <div className="panel-heading"><h2>Loaded-record summary</h2></div>
        <dl className="kv-list">
          <div><dt>Average findings per inspection</dt><dd>{average}</dd></div>
          <div><dt>Inspections with a reference board</dt><dd>{withReference} of {items.length}</dd></div>
          <div><dt>Strict pass rate</dt><dd>{data.passRate === null ? "—" : `${data.passRate}%`}</dd></div>
        </dl>
      </section>
    </div>
  );
}
