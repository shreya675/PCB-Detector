import { formatDate } from "../lib/analytics";
import type { InspectionSummary } from "../types";
import { StatusBadge } from "./StatusBadge";

interface HistoryTableProps {
  items: InspectionSummary[];
  onSelect: (id: string) => void;
}

export function HistoryTable({ items, onSelect }: HistoryTableProps) {
  if (!items.length) {
    return (
      <div className="empty-state">
        <strong>No inspections yet</strong>
        <span>Upload a PCB image to create the first inspection record.</span>
      </div>
    );
  }

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Inspection</th>
            <th>Timestamp</th>
            <th>Status</th>
            <th>Defects</th>
            <th>Reference</th>
            <th>Model</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const counts = item.summary.severity_counts || {};
            const critical = counts.critical || 0;
            return (
              <tr
                key={item.id}
                className="clickable"
                tabIndex={0}
                onClick={() => onSelect(item.id)}
                onKeyDown={(event) => { if (event.key === "Enter") onSelect(item.id); }}
              >
                <td><button className="row-link" tabIndex={-1}>#{item.id.slice(0, 8)}</button></td>
                <td>{formatDate(item.created_at)}</td>
                <td><StatusBadge value={item.status} /></td>
                <td>
                  {item.summary.defect_count ?? 0}
                  {critical > 0 && <span className="muted"> · {critical} critical</span>}
                </td>
                <td className="muted">{item.summary.reference_comparison ? "Yes" : "No"}</td>
                <td className="mono muted">{item.model_version.replace("sha256:", "")}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
