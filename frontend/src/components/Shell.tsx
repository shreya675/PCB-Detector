import { useState, type ReactNode } from "react";
import { Icon } from "./Icon";

export type View = "dashboard" | "new" | "history" | "analytics" | "model";

const NAV: { id: View; label: string; icon: Parameters<typeof Icon>[0]["name"] }[] = [
  { id: "dashboard", label: "Overview", icon: "grid" },
  { id: "new", label: "New inspection", icon: "scan" },
  { id: "history", label: "Inspection history", icon: "history" },
  { id: "analytics", label: "Defect analytics", icon: "analytics" },
  { id: "model", label: "Model performance", icon: "model" },
];

interface ShellProps {
  view: View;
  onView: (view: View) => void;
  children: ReactNode;
}

export function Shell({ view, onView, children }: ShellProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="app-shell">
      <aside className={open ? "sidebar sidebar-open" : "sidebar"}>
        <div className="brand">
          <span className="brand-mark">AOI</span>
          <div>
            <strong>PCB Inspector</strong>
            <small>Optical inspection</small>
          </div>
        </div>

        <div className="nav-caption">WORKSPACE</div>
        <nav aria-label="Primary navigation" id="workspace-navigation">
          {NAV.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? "nav-item active" : "nav-item"}
              aria-current={view === item.id ? "page" : undefined}
              onClick={() => { onView(item.id); setOpen(false); }}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="prototype-note">
          <strong>Research prototype</strong>
          Not certified for industrial acceptance decisions.
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} aria-controls="workspace-navigation" onClick={() => setOpen(!open)}>
            <Icon name="menu" />
          </button>
          <div className="topbar-title">Optical inspection <span className="topbar-divider">/</span> <span className="muted">{NAV.find((item) => item.id === view)?.label}</span></div>
        </header>
        <main className="page-content">{children}</main>
      </div>

      {open && <button className="backdrop" aria-label="Close menu" onClick={() => setOpen(false)} />}
    </div>
  );
}
