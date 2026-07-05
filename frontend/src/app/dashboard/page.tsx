import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";
import { Shell } from "@/components/Shell";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);
  if (!session) redirect("/login");

  return (
    <Shell title="dashboard" breadcrumb={["malaria-platform", "overview"]}>
      {/* KPI row */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {KPI_CARDS.map((card) => (
          <KpiCard key={card.label} {...card} />
        ))}
      </section>

      {/* Middle row: resource meters + recent jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Resource panel */}
        <div className="panel p-5 space-y-4">
          <p className="font-display font-semibold text-base" style={{ color: "rgba(255,255,255,0.88)" }}>
            Compute Resources
          </p>
          {RESOURCES.map((r) => (
            <ResourceBar key={r.label} {...r} />
          ))}
        </div>

        {/* Recent jobs */}
        <div className="panel p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <p className="font-display font-semibold text-base" style={{ color: "rgba(255,255,255,0.88)" }}>
              Recent Jobs
            </p>
            <span
              className="font-mono text-xs px-2 py-0.5 rounded"
              style={{ background: "rgba(70,180,255,0.10)", color: "#46B4FF" }}
            >
              LIVE
            </span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Pipeline</th>
                <th>Samples</th>
                <th>Status</th>
                <th>Progress</th>
              </tr>
            </thead>
            <tbody>
              {JOBS.map((job) => (
                <tr key={job.id}>
                  <td>
                    <span style={{ color: "#4CE0B3" }}>{job.id}</span>
                  </td>
                  <td style={{ color: "rgba(255,255,255,0.70)" }}>{job.pipeline}</td>
                  <td style={{ color: "rgba(255,255,255,0.50)" }}>{job.samples}</td>
                  <td>
                    <StatusPill status={job.status} />
                  </td>
                  <td style={{ minWidth: 80 }}>
                    <ProgressMini pct={job.pct} color={JOB_COLORS[job.status]} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {JOBS.length === 0 && (
            <p className="font-mono text-xs text-center py-8" style={{ color: "rgba(255,255,255,0.25)" }}>
              No jobs yet — submit a pipeline to get started
            </p>
          )}
        </div>
      </div>

      {/* Bottom row: sample table + activity log */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Sample table */}
        <div className="panel p-5 lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <p className="font-display font-semibold text-base" style={{ color: "rgba(255,255,255,0.88)" }}>
              Recent Samples
            </p>
            <a
              href="/dashboard/samples"
              className="font-mono text-xs hover:underline"
              style={{ color: "#4CE0B3" }}
            >
              View all →
            </a>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Sample ID</th>
                <th>Species</th>
                <th>Location</th>
                <th>Files</th>
              </tr>
            </thead>
            <tbody>
              {SAMPLES.map((s) => (
                <tr key={s.id}>
                  <td>
                    <span className="font-mono" style={{ color: "#46B4FF" }}>{s.id}</span>
                  </td>
                  <td style={{ color: "rgba(255,255,255,0.70)" }}>{s.species}</td>
                  <td style={{ color: "rgba(255,255,255,0.50)" }}>{s.location}</td>
                  <td style={{ color: "rgba(255,255,255,0.50)" }}>{s.files}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {SAMPLES.length === 0 && (
            <p className="font-mono text-xs text-center py-8" style={{ color: "rgba(255,255,255,0.25)" }}>
              No samples yet
            </p>
          )}
        </div>

        {/* Activity log */}
        <div className="panel p-5 lg:col-span-2">
          <p className="font-display font-semibold text-base mb-4" style={{ color: "rgba(255,255,255,0.88)" }}>
            Activity Log
          </p>
          <ul className="space-y-3">
            {ACTIVITY.map((ev, i) => (
              <li key={i} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div
                    className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                    style={{ background: ev.color }}
                  />
                  {i < ACTIVITY.length - 1 && (
                    <div className="w-px flex-1 mt-1" style={{ background: "#2A333E" }} />
                  )}
                </div>
                <div className="pb-3">
                  <p
                    className="font-mono text-xs leading-relaxed"
                    style={{ color: "rgba(255,255,255,0.70)" }}
                  >
                    {ev.message}
                  </p>
                  <p className="font-mono text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.25)" }}>
                    {ev.time}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Shell>
  );
}

/* ── Sub-components ───────────────────────────────────────── */

function KpiCard({
  label,
  value,
  delta,
  color,
  icon,
}: {
  label: string;
  value: string;
  delta?: string;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div
      className="rounded-lg p-5 flex flex-col gap-3"
      style={{ background: "#161B22", border: "1px solid #2A333E" }}
    >
      <div className="flex items-center justify-between">
        <p
          className="font-mono text-xs uppercase tracking-widest"
          style={{ color: "rgba(255,255,255,0.30)" }}
        >
          {label}
        </p>
        <div
          className="w-7 h-7 rounded flex items-center justify-center"
          style={{ background: `${color}15` }}
        >
          <span style={{ color }}>{icon}</span>
        </div>
      </div>
      <div>
        <p
          className="font-display text-3xl font-semibold"
          style={{ color: "rgba(255,255,255,0.92)" }}
        >
          {value}
        </p>
        {delta && (
          <p className="font-mono text-xs mt-1" style={{ color: "rgba(255,255,255,0.35)" }}>
            {delta}
          </p>
        )}
      </div>
    </div>
  );
}

function ResourceBar({
  label,
  used,
  total,
  unit,
  color,
}: {
  label: string;
  used: number;
  total: number;
  unit: string;
  color: string;
}) {
  const pct = Math.round((used / total) * 100);
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="font-mono text-xs" style={{ color: "rgba(255,255,255,0.50)" }}>
          {label}
        </span>
        <span className="font-mono text-xs" style={{ color: "rgba(255,255,255,0.70)" }}>
          {used}/{total} {unit}
        </span>
      </div>
      <div className="progress-track">
        <div
          className="progress-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

function ProgressMini({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="progress-track flex-1">
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="font-mono text-xs" style={{ color: "rgba(255,255,255,0.40)", minWidth: 28, textAlign: "right" }}>
        {pct}%
      </span>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, { bg: string; fg: string }> = {
    running: { bg: "rgba(76,224,179,0.12)", fg: "#4CE0B3" },
    queued: { bg: "rgba(70,180,255,0.12)", fg: "#46B4FF" },
    failed: { bg: "rgba(242,98,123,0.12)", fg: "#F2627B" },
    done: { bg: "rgba(167,139,250,0.12)", fg: "#A78BFA" },
  };
  const s = map[status] ?? map.queued;
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-mono text-xs"
      style={{ background: s.bg, color: s.fg }}
    >
      {status === "running" && (
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{ background: s.fg, animation: "pulse 2s ease-in-out infinite" }}
        />
      )}
      {status}
    </span>
  );
}

/* ── Static placeholder data ─────────────────────────────── */

const KPI_CARDS = [
  { label: "Total Samples", value: "—", color: "#4CE0B3", icon: "◈" },
  { label: "Active Projects", value: "—", color: "#46B4FF", icon: "⬡" },
  { label: "Running Jobs", value: "—", color: "#F2B544", icon: "↻" },
  { label: "Completed Analyses", value: "—", color: "#A78BFA", icon: "✓" },
];

const RESOURCES = [
  { label: "CPU cores", used: 0, total: 32, unit: "cores", color: "#4CE0B3" },
  { label: "Memory", used: 0, total: 128, unit: "GB", color: "#46B4FF" },
  { label: "Storage", used: 0, total: 500, unit: "GB", color: "#F2B544" },
];

const JOBS: {
  id: string;
  pipeline: string;
  samples: number;
  status: string;
  pct: number;
}[] = [];

const JOB_COLORS: Record<string, string> = {
  running: "#4CE0B3",
  queued: "#46B4FF",
  failed: "#F2627B",
  done: "#A78BFA",
};

const SAMPLES: {
  id: string;
  species: string;
  location: string;
  files: number;
}[] = [];

const ACTIVITY = [
  { message: "Platform initialised — database migrations applied", time: "just now", color: "#4CE0B3" },
  { message: "MinIO bucket genomics-data configured", time: "just now", color: "#46B4FF" },
  { message: "Keycloak realm malaria pending configuration", time: "just now", color: "#F2B544" },
  { message: "Celery workers standing by", time: "just now", color: "#A78BFA" },
];
