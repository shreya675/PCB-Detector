import { useState, type ReactNode } from "react";
import { Icon } from "./Icon";

type View = "dashboard" | "new" | "history" | "analytics" | "model";
const items: { id: View; label: string; icon: Parameters<typeof Icon>[0]["name"] }[] = [
  { id: "dashboard", label: "Dashboard", icon: "grid" },
  { id: "new", label: "New inspection", icon: "scan" },
  { id: "history", label: "Inspection history", icon: "history" },
  { id: "analytics", label: "Defect analytics", icon: "analytics" },
  { id: "model", label: "Model performance", icon: "model" },
];

export function Shell({ view, onView, children }: { view: View; onView: (view: View) => void; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return <div className="app-shell">
    <aside className={open ? "sidebar sidebar-open" : "sidebar"}>
      <div className="brand"><span className="brand-mark">AO</span><div><strong>Optic Inspector</strong><small>PCB AOI prototype</small></div></div>
      <nav aria-label="Primary navigation">{items.map((item) => <button key={item.id} className={view === item.id ? "nav-item active" : "nav-item"} onClick={() => { onView(item.id); setOpen(false); }}><Icon name={item.icon}/><span>{item.label}</span></button>)}</nav>
      <div className="prototype-note"><strong>Research prototype</strong><span>Not certified for industrial acceptance decisions.</span></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><button className="icon-button mobile-menu" aria-label="Open menu" onClick={() => setOpen(!open)}><Icon name="menu"/></button><div className="topbar-title">PCB optical inspection</div><div className="operator"><span className="operator-dot"/>Engineering console</div></header>
      <div className="page-content">{children}</div>
    </div>
    {open && <button className="backdrop" aria-label="Close menu" onClick={() => setOpen(false)}/>}
  </div>;
}
