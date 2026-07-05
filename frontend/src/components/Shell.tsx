"use client";

import { Sidebar } from "./Sidebar";

interface ShellProps {
  children: React.ReactNode;
  title?: string;
  breadcrumb?: string[];
  actions?: React.ReactNode;
}

export function Shell({ children, title, breadcrumb, actions }: ShellProps) {
  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />

      {/* Main area offset by sidebar width */}
      <div className="flex flex-col flex-1 min-w-0" style={{ marginLeft: 220 }}>
        {/* Topbar */}
        <header className="topbar">
          <div className="flex items-center gap-2 font-mono text-xs text-ink-muted">
            {breadcrumb ? (
              breadcrumb.map((crumb, i) => (
                <span key={i} className="flex items-center gap-2">
                  {i > 0 && <span className="text-ink-faint">/</span>}
                  <span className={i === breadcrumb.length - 1 ? "text-ink" : ""}>{crumb}</span>
                </span>
              ))
            ) : (
              <>
                <span>malaria-platform</span>
                <span className="text-ink-faint">/</span>
                <span className="text-ink">{title ?? "dashboard"}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* System status pill */}
            <div className="pill-signal">
              <span className="dot-signal" />
              All systems operational
            </div>
            {actions}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
