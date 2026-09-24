import { useCallback, useEffect, useState } from "react";
import { api } from "./lib/api";
import { summarizeInspections } from "./lib/analytics";
import type { HealthResponse, Inspection, InspectionSummary, ModelInfo } from "./types";
import { AnalyticsPanel, BarList } from "./components/AnalyticsPanel";
import { HistoryTable } from "./components/HistoryTable";
import { Icon } from "./components/Icon";
import { InspectionResult } from "./components/InspectionResult";
import { MetricCard } from "./components/MetricCard";
import { ModelPanel } from "./components/ModelPanel";
import { Shell, type View } from "./components/Shell";
import { UploadPanel } from "./components/UploadPanel";

const PAGE_TITLES: Record<View, { title: string; subtitle: string }> = {
  dashboard: { title: "Inspection overview", subtitle: "Review your boards, check findings, and pick up where you left off." },
  new: { title: "New inspection", subtitle: "Choose a board image to check for defects." },
  history: { title: "Inspection history", subtitle: "Open a record to review the board image and its findings." },
  analytics: { title: "Defect analytics", subtitle: "A closer look at outcomes and defect severity." },
  model: { title: "Model performance", subtitle: "Loaded weights and their held-out evaluation results." },
};

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
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
    const results = await Promise.allSettled([api.health(), api.inspections(), api.model()]);
    setHealth(results[0].status === "fulfilled" ? results[0].value : null);
    if (results[1].status === "fulfilled") {
      setItems(results[1].value.items);
      setTotal(results[1].value.total);
    }
    setModelInfo(results[2].status === "fulfilled" ? results[2].value : null);
    if (results[0].status === "rejected" || results[1].status === "rejected") {
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
      <Shell view="history" onView={(next) => { setSelected(null); setView(next); }}>
        <InspectionResult inspection={selected} onBack={() => setSelected(null)} />
      </Shell>
    );
  }

  const summary = summarizeInspections(items);
  const page = PAGE_TITLES[view];
  const showsRecords = view === "dashboard" || view === "history" || view === "analytics";

  return (
    <Shell view={view} onView={setView}>
      <div className="page-header">
        <div>
          <div className="eyebrow">PCB INSPECTOR / WORKSPACE</div>
          <h1>{page.title}</h1>
          <p>{page.subtitle}</p>
        </div>
        <div className="header-actions">
        <button className="secondary-button" onClick={() => void refresh()} disabled={loading}>
          <Icon name="refresh" />
          {loading ? "Refreshing…" : "Refresh"}
        </button>
        {view !== "new" && <button className="primary-button" onClick={() => setView("new")}><Icon name="scan" />New inspection</button>}
        </div>
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
              <MetricCard label="Boards inspected" value={total} note="All saved records" />
              <MetricCard label="Pass rate" value={summary.passRate === null ? "—" : `${summary.passRate}%`} note={`Without warnings · ${items.length} loaded`} tone="green" />
              <MetricCard label="Defects found" value={summary.defects} note="In loaded records" tone="orange" />
              <MetricCard label="Critical findings" value={summary.severity.critical} note="In loaded records" tone="red" />
            </div>

            <section className="panel">
              <div className="panel-heading">
                <div><div className="eyebrow">INSPECTION LOG</div><h2>Latest inspections</h2></div>
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
                <div className="panel-heading">
                  <h2>Findings by severity</h2>
                  <span>{summary.defects} total</span>
                </div>
                {items.length ? (
                  <BarList
                    label={`Critical ${summary.severity.critical}, major ${summary.severity.major}, minor ${summary.severity.minor}`}
                    rows={[
                      ["Critical", summary.severity.critical, "red"],
                      ["Major", summary.severity.major, "orange"],
                      ["Minor", summary.severity.minor, "blue"],
                    ] as const}
                  />
                ) : (
                  <div className="loading-text">No inspections yet. Run one to see the breakdown.</div>
                )}
              </section>

              <section className="panel action-panel">
                <div className="eyebrow">AT THE BENCH</div>
                <h2>Start with a clear board image.</h2>
                <p>Keep the whole board in frame. Add a reference board if you need alignment and comparison.</p>
                <div className="bench-note"><Icon name="scan" /><span>PNG, JPEG, BMP or TIFF<br /><span className="muted">Up to 20 MB per image</span></span></div>
                <button className="text-button" onClick={() => setView("new")}>Choose board image <span aria-hidden="true">→</span></button>
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

        {view === "model" && <ModelPanel info={modelInfo} apiVersion={health?.version} />}
      </div>
    </Shell>
  );
}
