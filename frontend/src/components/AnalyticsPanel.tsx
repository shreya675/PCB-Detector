import { summarizeInspections } from "../lib/analytics";
import type { InspectionSummary } from "../types";

export function AnalyticsPanel({ items }: { items: InspectionSummary[] }) {
  const data = summarizeInspections(items);
  const statusValues = [
    ["Pass", data.status.pass, "green"], ["Warning", data.status.warning, "orange"], ["Fail", data.status.fail, "red"],
  ] as const;
  const severityValues = [
    ["Critical", data.severity.critical, "red"], ["Major", data.severity.major, "orange"], ["Minor", data.severity.minor, "blue"],
  ] as const;
  const maxStatus = Math.max(1, ...statusValues.map((item) => item[1]));
  const maxSeverity = Math.max(1, ...severityValues.map((item) => item[1]));
  return <div className="analytics-grid">
    <section className="panel chart-panel"><div className="panel-heading"><div><span className="eyebrow">OUTCOMES</span><h2>Inspection status</h2></div><span>{items.length} records</span></div><div className="bar-list" role="img" aria-label={`Pass ${data.status.pass}, warning ${data.status.warning}, fail ${data.status.fail}`}>{statusValues.map(([name, value, tone]) => <div className="bar-row" key={name}><div className="bar-meta"><span>{name}</span><strong>{value}</strong></div><div className="bar-track"><span className={`bar-fill fill-${tone}`} style={{ width: `${(value / maxStatus) * 100}%` }}/></div></div>)}</div></section>
    <section className="panel chart-panel"><div className="panel-heading"><div><span className="eyebrow">SEVERITY</span><h2>Observed findings</h2></div><span>{data.defects} total</span></div><div className="bar-list" role="img" aria-label={`Critical ${data.severity.critical}, major ${data.severity.major}, minor ${data.severity.minor}`}>{severityValues.map(([name, value, tone]) => <div className="bar-row" key={name}><div className="bar-meta"><span>{name}</span><strong>{value}</strong></div><div className="bar-track"><span className={`bar-fill fill-${tone}`} style={{ width: `${(value / maxSeverity) * 100}%` }}/></div></div>)}</div></section>
  </div>;
}
