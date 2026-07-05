"use client";

import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function LoginContent() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/dashboard";

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: "#0E1116" }}
    >
      {/* Subtle grid background */}
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(76,224,179,1) 1px, transparent 1px), linear-gradient(90deg, rgba(76,224,179,1) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative w-full max-w-sm px-4">
        {/* Card */}
        <div
          className="rounded-xl border p-8"
          style={{
            background: "#161B22",
            borderColor: "#2A333E",
            boxShadow: "0 0 40px rgba(76,224,179,0.06)",
          }}
        >
          {/* Logo + wordmark */}
          <div className="flex flex-col items-center gap-4 mb-8">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(76,224,179,0.10)", border: "1px solid rgba(76,224,179,0.25)" }}
            >
              <DnaIcon />
            </div>
            <div className="text-center">
              <h1
                className="font-display font-semibold text-xl"
                style={{ color: "rgba(255,255,255,0.9)" }}
              >
                BioVis<span style={{ color: "#4CE0B3" }}>.</span>
              </h1>
              <p
                className="font-mono text-xs mt-0.5 uppercase tracking-widest"
                style={{ color: "rgba(255,255,255,0.30)" }}
              >
                Malaria Genomics Platform
              </p>
            </div>
          </div>

          {/* System status */}
          <div
            className="flex items-center gap-2 rounded px-3 py-2 mb-6 font-mono text-xs"
            style={{
              background: "rgba(76,224,179,0.06)",
              border: "1px solid rgba(76,224,179,0.15)",
              color: "#4CE0B3",
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full bg-signal"
              style={{ animation: "pulse 2s ease-in-out infinite" }}
            />
            All systems nominal — Keycloak auth ready
          </div>

          {/* Sign in button */}
          <button
            onClick={() => signIn("keycloak", { callbackUrl })}
            className="w-full rounded-lg py-2.5 font-mono text-sm font-medium transition-all duration-150 active:scale-[0.98]"
            style={{
              background: "#4CE0B3",
              color: "#0E1116",
              boxShadow: "0 0 0 0 rgba(76,224,179,0.4)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.boxShadow =
                "0 0 20px rgba(76,224,179,0.3)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.boxShadow = "none";
            }}
          >
            Sign in via Institutional SSO
          </button>

          <p
            className="text-center font-mono text-xs mt-5"
            style={{ color: "rgba(255,255,255,0.25)" }}
          >
            Accounts are managed by your institution&apos;s identity provider.
          </p>
        </div>

        {/* Footer */}
        <p
          className="text-center font-mono text-xs mt-5"
          style={{ color: "rgba(255,255,255,0.20)" }}
        >
          BGI · Beijing Genomics Institute · v0.1.0
        </p>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  );
}

function DnaIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4CE0B3" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 15c6.667-6 13.333 6 20 0" />
      <path d="M2 9c6.667-6 13.333 6 20 0" />
      <path d="M5 17.5v2" /><path d="M19 17.5v2" />
      <path d="M5 4.5v2" /><path d="M19 4.5v2" />
    </svg>
  );
}
