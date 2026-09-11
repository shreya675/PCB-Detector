import type { HealthResponse, Inspection, InspectionList } from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      if (typeof payload.detail === "string") message = payload.detail;
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  inspections: (limit = 50, offset = 0) =>
    request<InspectionList>(`/api/inspections?limit=${limit}&offset=${offset}`),
  inspection: (id: string) => request<Inspection>(`/api/inspections/${id}`),
  inspect: (test: File, reference?: File) => {
    const body = new FormData();
    body.append("test_image", test);
    if (reference) body.append("reference_image", reference);
    return request<Inspection>("/api/inspect", { method: "POST", body });
  },
  imageUrl: (id: string, kind: "test" | "reference" | "annotated") =>
    `${API_BASE}/api/inspections/${id}/image/${kind}`,
  reportUrl: (id: string) => `${API_BASE}/api/inspections/${id}/report`,
};
