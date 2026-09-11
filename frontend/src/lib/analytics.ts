import type { InspectionSummary, Severity } from "../types";

export function summarizeInspections(items: InspectionSummary[]) {
  const status = { pass: 0, warning: 0, fail: 0 };
  const severity: Record<Severity, number> = { critical: 0, major: 0, minor: 0 };
  let defects = 0;
  for (const item of items) {
    if (item.status === "PASS") status.pass += 1;
    else if (item.status === "FAIL") status.fail += 1;
    else status.warning += 1;
    defects += item.summary.defect_count || 0;
    for (const level of Object.keys(severity) as Severity[]) {
      severity[level] += item.summary.severity_counts?.[level] || 0;
    }
  }
  const passRate = items.length ? Math.round((status.pass / items.length) * 100) : null;
  return { status, severity, defects, passRate };
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
