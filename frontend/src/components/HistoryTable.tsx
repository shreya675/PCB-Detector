import { formatDate } from "../lib/analytics";
import type { InspectionSummary } from "../types";
import { StatusBadge } from "./StatusBadge";

export function HistoryTable({ items, onSelect }: { items: InspectionSummary[]; onSelect: (id: string) => void }) {
  if (!items.length) return <div className="empty-state"><strong>No inspections yet</strong><span>Upload a PCB image to create the first inspection record.</span></div>;
  return <div className="table-scroll"><table><thead><tr><th>Inspection</th><th>Timestamp</th><th>Status</th><th>Defects</th><th>Model</th></tr></thead><tbody>{items.map((item) => <tr key={item.id} onClick={() => onSelect(item.id)} tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter") onSelect(item.id); }}><td><button className="row-link">#{item.id.slice(0, 8)}</button></td><td>{formatDate(item.created_at)}</td><td><StatusBadge value={item.status}/></td><td>{item.summary.defect_count ?? 0}</td><td className="mono">{item.model_version}</td></tr>)}</tbody></table></div>;
}
