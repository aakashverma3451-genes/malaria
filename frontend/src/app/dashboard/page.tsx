import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);
  if (!session) redirect("/login");

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">
          Welcome back. Platform is ready — full pages come in Stage 5.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
          {[
            { label: "Projects", value: "—" },
            { label: "Samples", value: "—" },
            { label: "Running Analyses", value: "—" },
            { label: "Completed", value: "—" },
          ].map((card) => (
            <div
              key={card.label}
              className="bg-white rounded-lg border border-slate-200 shadow-sm p-5"
            >
              <p className="text-sm text-slate-500">{card.label}</p>
              <p className="text-3xl font-bold text-slate-900 mt-1">{card.value}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
