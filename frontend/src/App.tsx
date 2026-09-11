import { useCallback, useEffect, useState } from "react";
import { api } from "./lib/api";
import { summarizeInspections } from "./lib/analytics";
import type { HealthResponse, Inspection, InspectionSummary } from "./types";
import { AnalyticsPanel } from "./components/AnalyticsPanel";
import { HistoryTable } from "./components/HistoryTable";
import { Icon } from "./components/Icon";
import { InspectionResult } from "./components/InspectionResult";
import { MetricCard } from "./components/MetricCard";
import { Shell } from "./components/Shell";
import { StatusBadge } from "./components/StatusBadge";
import { UploadPanel } from "./components/UploadPanel";

type View = "dashboard" | "new" | "history" | "analytics" | "model";

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
    setLoading(true); setError(null);
    const results = await Promise.allSettled([api.health(), api.inspections()]);
    if (results[0].status === "fulfilled") setHealth(results[0].value);
    else setHealth(null);
    if (results[1].status === "fulfilled") { setItems(results[1].value.items); setTotal(results[1].value.total); }
    const failed = results.filter((result) => result.status === "rejected");
    if (failed.length) setError("Unable to refresh inspection services. Check the API connection; previously loaded records may be stale.");
    setLoading(false);
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  async function loadMore() {
    setLoadingMore(true); setError(null);
    try {
      const page = await api.inspections(50, items.length);
      setItems((current) => [...current, ...page.items.filter((item) => !current.some((existing) => existing.id === item.id))]);
      setTotal(page.total);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load more records"); }
    finally { setLoadingMore(false); }
  }
  async function openInspection(id: string) {
    setError(null);
    try { setSelected(await api.inspection(id)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load inspection"); }
  }
  async function submit(test: File, reference?: File) {
    setBusy(true); setError(null);
    try { const result = await api.inspect(test, reference); setSelected(result); await refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Inspection failed"); }
    finally { setBusy(false); }
  }
  if (selected) return <Shell view="history" onView={(next) => { setSelected(null); setView(next); }}><InspectionResult inspection={selected} onBack={() => setSelected(null)}/></Shell>;

  const summary = summarizeInspections(items);
  return <Shell view={view} onView={setView}>
    <div className="page-header"><div><span className="eyebrow">AOI CONTROL CENTER</span><h1>{view === "dashboard" ? "Inspection overview" : view === "new" ? "New inspection" : view === "history" ? "Inspection history" : view === "analytics" ? "Defect analytics" : "Model performance"}</h1><p>{view === "dashboard" ? "Monitor inspection outcomes, defects, and system readiness." : "Academic PCB inspection workspace."}</p></div><button className="secondary-button" onClick={() => void refresh()} disabled={loading}><Icon name="refresh"/>Refresh</button></div>
    {error && <div className="error-banner" role="alert">{error}</div>}
    {["dashboard", "history", "analytics"].includes(view) && <div className="info-banner">Showing {items.length} of {total} inspections. Analytics describe loaded records.{items.length < total && <button className="text-button" onClick={() => void loadMore()} disabled={loadingMore || loading}>{loadingMore ? "Loading..." : "Load more inspections"}</button>}</div>}
    {view === "dashboard" && <div className="stack"><div className="metrics-grid"><MetricCard label="Total inspections" value={total} note="Stored inspection records"/><MetricCard label="Pass rate" value={summary.passRate === null ? "—" : `${summary.passRate}%`} note={`Strict PASS across ${items.length} loaded records`} tone="green"/><MetricCard label="Recorded findings" value={summary.defects} note="Across loaded inspections" tone="orange"/><MetricCard label="Critical" value={summary.severity.critical} note="Critical findings observed" tone="red"/></div><section className="panel"><div className="panel-heading"><div><span className="eyebrow">RECENT ACTIVITY</span><h2>Latest inspections</h2></div><button className="text-button" onClick={() => setView("history")}>View all →</button></div>{loading ? <div className="loading-line"/> : <HistoryTable items={items.slice(0, 6)} onSelect={(id) => void openInspection(id)}/>}</section><div className="system-grid"><section className="panel system-panel"><div><span className="eyebrow">SYSTEM STATUS</span><h2>Inspection services</h2></div><dl><div><dt>API</dt><dd><StatusBadge value={health?.status === "ok" ? "online" : "offline"}/></dd></div><div><dt>Database</dt><dd>{health?.database || "Unavailable"}</dd></div><div><dt>Detection model</dt><dd>{health?.model_status || "Unknown"}</dd></div></dl></section><section className="panel action-panel"><span className="eyebrow">QUICK ACTION</span><h2>Inspect a new PCB</h2><p>Upload a test board and optional reference image to begin.</p><button className="primary-button" onClick={() => setView("new")}>Start inspection</button></section></div></div>}
    {view === "new" && <UploadPanel busy={busy} error={error} onSubmit={submit}/>} 
    {view === "history" && <section className="panel"><div className="panel-heading"><div><span className="eyebrow">ARCHIVE</span><h2>All inspections</h2></div><span>{total} records</span></div><HistoryTable items={items} onSelect={(id) => void openInspection(id)}/></section>}
    {view === "analytics" && <AnalyticsPanel items={items}/>} 
    {view === "model" && <section className="panel model-panel"><div className="model-icon"><Icon name="model"/></div><span className="eyebrow">MODEL READINESS</span><h2>{health?.model_status === "available" ? "Detection model available" : "No evaluated project model available"}</h2><p>{health?.model_status === "available" ? "A weights file is configured. Review its model card and evaluation artifacts before interpreting results." : "Train and evaluate the Phase 3 baseline to populate model version and performance evidence."}</p><div className="model-facts"><div><span>API version</span><strong>{health?.version || "Unavailable"}</strong></div><div><span>Environment</span><strong>{health?.environment || "Unavailable"}</strong></div><div><span>Certification</span><strong>None · research only</strong></div></div><div className="info-banner">Performance metrics remain intentionally empty until a reproducible evaluation run is available. No placeholder accuracy is shown.</div></section>}
  </Shell>;
}
