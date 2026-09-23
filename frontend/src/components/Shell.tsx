import { useState, type ReactNode } from "react";
import type { HealthResponse } from "../types";
import { Icon } from "./Icon";
import { StatusBadge } from "./StatusBadge";

export type View = "dashboard" | "new" | "history" | "analytics" | "model";

const NAV: { id: View; label: string; icon: Parameters<typeof Icon>[0]["name"] }[] = [
  { id: "dashboard", label: "Dashboard", icon: "grid" },
  { id: "new", label: "New inspection", icon: "scan" },
  { id: "history", label: "Inspection history", icon: "history" },
  { id: "analytics", label: "Defect analytics", icon: "analytics" },
  { id: "model", label: "Model performance", icon: "model" },
];

interface ShellProps {
  view: View;
  health: HealthResponse | null;
  onView: (view: View) => void;
  children: ReactNode;
}

export function Shell({ view, health, onView, children }: ShellProps) {
  const [open, setOpen] = useState(false);
  const apiOnline = health?.status === "ok";

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

        <nav aria-label="Primary navigation">
          {NAV.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? "nav-item active" : "nav-item"}
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
          <button className="icon-button mobile-menu" aria-label="Open menu" onClick={() => setOpen(!open)}>
            <Icon name="menu" />
          </button>
          <div className="topbar-title">PCB optical inspection</div>
          <div className="topbar-right">
            <span className="muted" style={{ fontSize: 13 }}>API</span>
            <StatusBadge value={health === null ? "offline" : apiOnline ? "online" : "degraded"} />
          </div>
        </header>
        <div className="page-content">{children}</div>
      </div>

      {open && <button className="backdrop" aria-label="Close menu" onClick={() => setOpen(false)} />}
    </div>
  );
}
