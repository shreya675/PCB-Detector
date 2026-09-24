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

export interface MetricPoint {
  precision: number;
  recall: number;
  tp?: number;
  fp?: number;
  fn?: number;
}

export interface ModelCard {
  name: string;
  architecture: string;
  trained_on?: string;
  dataset: {
    name: string;
    split: string;
    train: number;
    val: number;
    test: number;
    image_size: number;
    classes: string[];
    untrained_classes?: string[];
  };
  training?: Record<string, string | number>;
  evaluation: {
    split: string;
    ultralytics_val: { conf: number; iou: number; precision: number; recall: number; mAP50: number; mAP50_95: number };
    operating_point: {
      conf: number;
      match_iou: number;
      note?: string;
      model_only: MetricPoint;
      with_postprocess: MetricPoint;
      defect_level_with_postprocess: MetricPoint;
    };
    per_class_with_postprocess: Record<string, MetricPoint>;
    reference?: { paper: string; precision: number; recall: number };
  };
  known_limitations?: string[];
}

export interface ModelInfo {
  model_status: "available" | "missing";
  weights_file: string;
  model_version: string;
  confidence_threshold: number;
  postprocess: { enabled: boolean; nms_iou: number; box_scale: number };
  evaluation: ModelCard | null;
  evaluation_mismatch: boolean;
}
