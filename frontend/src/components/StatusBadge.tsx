import type { InspectionStatus, Severity } from "../types";

type BadgeValue = InspectionStatus | Severity | "online" | "offline" | "degraded" | "available" | "missing";

export function StatusBadge({ value, large = false }: { value: BadgeValue; large?: boolean }) {
  const key = value.toLowerCase().replaceAll(" ", "-");
  return (
    <span className={`status-badge status-${key}${large ? " large" : ""}`}>
      <span className="status-dot" />
      {value}
    </span>
  );
}
