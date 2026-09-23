import { useCallback, useEffect, useState } from "react";
import { api } from "./lib/api";
import { summarizeInspections } from "./lib/analytics";
import type { HealthResponse, Inspection, InspectionSummary } from "./types";
import { AnalyticsPanel } from "./components/AnalyticsPanel";
import { HistoryTable } from "./components/HistoryTable";
import { Icon } from "./components/Icon";
import { InspectionResult } from "./components/InspectionResult";
import { MetricCard } from "./components/MetricCard";
import { Shell, type View } from "./components/Shell";
import { StatusBadge } from "./components/StatusBadge";
import { UploadPanel } from "./components/UploadPanel";

const PAGE_TITLES: Record<View, { title: string; subtitle: string }> = {
  dashboard: { title: "Inspection overview", subtitle: "Monitor inspection outcomes, defects, and system readiness." },
  new: { title: "New inspection", subtitle: "Upload a board image to run the detection pipeline." },
  history: { title: "Inspection history", subtitle: "Every stored inspection record, newest first." },
  analytics: { title: "Defect analytics", subtitle: "Outcome and severity breakdown of the loaded records." },
  model: { title: "Model performance", subtitle: "Detection model readiness and declared output classes." },
};

const MODEL_CLASSES = [
  "open_circuit", "short_circuit", "spur", "spurious_copper", "mouse_bite", "missing_hole", "pin_hole",
];

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [items, setItems] = useState<InspectionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<Inspection | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    const results = await Promise.allSettled([api.health(), api.inspections()]);
    setHealth(results[0].status === "fulfilled" ? results[0].value : null);
    if (results[1].status === "fulfilled") {
      setItems(results[1].value.items);
      setTotal(results[1].value.total);
    }
    if (results.some((result) => result.status === "rejected")) {
      setError("Unable to reach the inspection API. Check that the backend is running; previously loaded records may be stale.");
    }
    setLoading(false);
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  async function loadMore() {
    setLoadingMore(true);
    setError(null);
    try {
      const page = await api.inspections(50, items.length);
      setItems((current) => [...current, ...page.items.filter((item) => !current.some((existing) => existing.id === item.id))]);
      setTotal(page.total);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load more records");
    } finally {
      setLoadingMore(false);
    }
  }

  async function openInspection(id: string) {
    setError(null);
    try {
      setSelected(await api.inspection(id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load inspection");
    }
  }

  async function submit(test: File, reference?: File) {
    setBusy(true);
    setError(null);
    try {
      const result = await api.inspect(test, reference);
      setSelected(result);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Inspection failed");
    } finally {
      setBusy(false);
    }
  }

  const modelAvailable = health?.model_status === "available";

  if (selected) {
    return (
      <Shell view="history" health={health} onView={(next) => { setSelected(null); setView(next); }}>
        <InspectionResult inspection={selected} onBack={() => setSelected(null)} />
      </Shell>
    );
  }

  const summary = summarizeInspections(items);
  const page = PAGE_TITLES[view];
  const showsRecords = view === "dashboard" || view === "history" || view === "analytics";

  return (
    <Shell view={view} health={health} onView={setView}>
      <div className="page-header">
        <div>
          <h1>{page.title}</h1>
          <p>{page.subtitle}</p>
        </div>
        <button className="secondary-button" onClick={() => void refresh()} disabled={loading}>
          <Icon name="refresh" />
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {error && view !== "new" && <div className="error-banner" role="alert">{error}</div>}

      {showsRecords && items.length < total && (
        <div className="info-banner">
          <span>Showing {items.length} of {total} inspections. Analytics describe loaded records only.</span>
          <button className="text-button" onClick={() => void loadMore()} disabled={loadingMore || loading}>
            {loadingMore ? "Loading…" : "Load more"}
          </button>
        </div>
      )}

      <div className="stack" style={{ marginTop: error || (showsRecords && items.length < total) ? 16 : 0 }}>
        {view === "dashboard" && (
          <>
            <div className="metrics-grid">
              <MetricCard label="Total inspections" value={total} note="Stored inspection records" />
              <MetricCard label="Pass rate" value={summary.passRate === null ? "—" : `${summary.passRate}%`} note={`Strict PASS across ${items.length} loaded records`} tone="green" />
              <MetricCard label="Findings" value={summary.defects} note="Across loaded inspections" tone="orange" />
              <MetricCard label="Critical" value={summary.severity.critical} note="Critical findings observed" tone="red" />
            </div>

            <section className="panel">
              <div className="panel-heading">
                <h2>Latest inspections</h2>
                <button className="text-button" onClick={() => setView("history")}>View all →</button>
              </div>
              {loading && !items.length ? (
                <div className="loading-text">Loading inspections…</div>
              ) : (
                <HistoryTable items={items.slice(0, 6)} onSelect={(id) => void openInspection(id)} />
              )}
            </section>

            <div className="system-grid">
              <section className="panel">
                <div className="panel-heading"><h2>System status</h2></div>
                <dl className="kv-list">
                  <div><dt>API</dt><dd><StatusBadge value={health === null ? "offline" : health.status === "ok" ? "online" : "degraded"} /></dd></div>
                  <div><dt>Database</dt><dd>{health?.database ?? "Unavailable"}</dd></div>
                  <div><dt>Detection model</dt><dd>{health ? <StatusBadge value={health.model_status} /> : "Unknown"}</dd></div>
                  <div><dt>Environment</dt><dd>{health?.environment ?? "—"}</dd></div>
                </dl>
              </section>

              <section className="panel action-panel">
                <h2>Inspect a new PCB</h2>
                <p>Upload a test board and an optional reference image to run the detection pipeline.</p>
                <button className="primary-button" onClick={() => setView("new")}>
                  <Icon name="scan" />
                  Start inspection
                </button>
              </section>
            </div>
          </>
        )}

        {view === "new" && (
          <UploadPanel busy={busy} error={error} modelAvailable={modelAvailable} onSubmit={submit} />
        )}

        {view === "history" && (
          <section className="panel">
            <div className="panel-heading">
              <h2>All inspections</h2>
              <span>{total} records</span>
            </div>
            {loading && !items.length ? (
              <div className="loading-text">Loading inspections…</div>
            ) : (
              <HistoryTable items={items} onSelect={(id) => void openInspection(id)} />
            )}
          </section>
        )}

        {view === "analytics" && <AnalyticsPanel items={items} />}

        {view === "model" && (
          <section className="panel model-panel">
            <div className="model-head">
              <div className="model-icon"><Icon name="model" /></div>
              <div>
                <h2>{modelAvailable ? "Detection model loaded" : "No evaluated project model available"}</h2>
                <span className="muted" style={{ fontSize: 13 }}>Ultralytics YOLO object detector</span>
              </div>
            </div>
            <p>
              {modelAvailable
                ? "A weights file is configured on the server. Review its training run and held-out evaluation before interpreting results."
                : "Train and evaluate the baseline, then place the weights at the configured model path to enable inspections."}
            </p>

            <div className="model-facts">
              <div><span>Model status</span><strong>{health ? <StatusBadge value={health.model_status} /> : "Unknown"}</strong></div>
              <div><span>API version</span><strong>{health?.version ?? "Unavailable"}</strong></div>
              <div><span>Certification</span><strong>None · research only</strong></div>
            </div>

            <h2 style={{ fontSize: 15 }}>Declared output classes</h2>
            <div className="class-list">
              {MODEL_CLASSES.map((name) => <span className="class-chip" key={name}>{name}</span>)}
            </div>

            <div className="info-banner">
              Accuracy metrics are shown only from a reproducible held-out evaluation run. None is bundled with the dashboard, so no placeholder numbers are displayed.
            </div>
          </section>
        )}
      </div>
    </Shell>
  );
}
