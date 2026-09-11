import type { InspectionStatus, Severity } from "../types";

export function StatusBadge({ value }: { value: InspectionStatus | Severity | "online" | "offline" }) {
  const key = value.toLowerCase().replaceAll(" ", "-");
  return <span className={`status-badge status-${key}`}><span className="status-dot" />{value}</span>;
}
