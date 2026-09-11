import type { Defect } from "../types";
import { StatusBadge } from "./StatusBadge";

function label(value: string) { return value.replaceAll("_", " "); }
export function DefectTable({ defects }: { defects: Defect[] }) {
  if (!defects.length) return <div className="empty-state compact"><strong>No defects detected</strong><span>The configured inspection pipeline returned no findings.</span></div>;
  return <div className="table-scroll"><table><thead><tr><th>Defect</th><th>Severity</th><th>Confidence</th><th>Location</th><th>Source</th></tr></thead><tbody>{defects.map((item) => <tr key={item.id}><td className="capitalize">{label(item.defect_type)}</td><td><StatusBadge value={item.severity}/></td><td>{item.confidence === null ? "Heuristic" : `${Math.round(item.confidence * 100)}%`}</td><td className="mono">{Math.round(item.bbox.x_min)}, {Math.round(item.bbox.y_min)} → {Math.round(item.bbox.x_max)}, {Math.round(item.bbox.y_max)}</td><td>{label(item.source)}</td></tr>)}</tbody></table></div>;
}
