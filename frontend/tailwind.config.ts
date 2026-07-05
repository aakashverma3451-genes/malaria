import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0E1116",
        panel: "#161B22",
        "panel-2": "#1C232D",
        border: "#2A333E",
        signal: {
          DEFAULT: "#4CE0B3",
          dim: "rgba(76,224,179,0.12)",
          muted: "rgba(76,224,179,0.35)",
        },
        "signal-2": {
          DEFAULT: "#46B4FF",
          dim: "rgba(70,180,255,0.12)",
        },
        amber: {
          DEFAULT: "#F2B544",
          dim: "rgba(242,181,68,0.12)",
        },
        rose: {
          DEFAULT: "#F2627B",
          dim: "rgba(242,98,123,0.12)",
        },
        violet: {
          DEFAULT: "#A78BFA",
          dim: "rgba(167,139,250,0.12)",
        },
        ink: {
          DEFAULT: "rgba(255,255,255,0.88)",
          muted: "rgba(255,255,255,0.50)",
          faint: "rgba(255,255,255,0.25)",
        },
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
        display: ["Space Grotesk", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["10px", "14px"],
        xs: ["11px", "16px"],
        sm: ["12px", "18px"],
        base: ["13px", "20px"],
        md: ["14px", "22px"],
        lg: ["16px", "24px"],
        xl: ["20px", "28px"],
        "2xl": ["24px", "32px"],
        "3xl": ["30px", "38px"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        lg: "8px",
        xl: "12px",
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(255,255,255,0.06)",
        glow: "0 0 16px rgba(76,224,179,0.18)",
        "glow-sm": "0 0 8px rgba(76,224,179,0.12)",
      },
      keyframes: {
        pulse_soft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.45" },
        },
        fade_in: {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        scan: {
          "0%": { backgroundPosition: "0% 0%" },
          "100%": { backgroundPosition: "0% 100%" },
        },
      },
      animation: {
        pulse_soft: "pulse_soft 2.4s ease-in-out infinite",
        fade_in: "fade_in 0.25s ease both",
        scan: "scan 8s linear infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
