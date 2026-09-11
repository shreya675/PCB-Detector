export type InspectionStatus = "PASS" | "PASS WITH WARNING" | "FAIL";
export type Severity = "critical" | "major" | "minor";

export interface HealthResponse {
  status: "ok" | "degraded";
  environment: string;
  version: string;
  database: string;
  model_status: "available" | "missing";
  prototype: boolean;
}

export interface Defect {
  id: number;
  defect_type: string;
  confidence: number | null;
  severity: Severity;
  source: string;
  bbox: { x_min: number; y_min: number; x_max: number; y_max: number };
  details: Record<string, unknown> | null;
}

export interface InspectionSummary {
  id: string;
  status: InspectionStatus;
  created_at: string;
  model_version: string;
  summary: {
    defect_count?: number;
    severity_counts?: Partial<Record<Severity, number>>;
    reference_comparison?: boolean;
    coverage_warning?: string;
    coordinate_frame?: string;
    heuristic_count?: number;
  };
}

export interface Inspection extends InspectionSummary {
  test_image_path: string;
  reference_image_path: string | null;
  annotated_image_path: string;
  report_path: string | null;
  alignment_quality: Record<string, number | string | boolean | null> | null;
  defects: Defect[];
}

export interface InspectionList {
  items: InspectionSummary[];
  total: number;
  limit: number;
  offset: number;
}
