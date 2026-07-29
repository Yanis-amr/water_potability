/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B1F26",
        panel: "#0F2A32",
        panel2: "#123B44",
        line: "#1E4A54",
        aqua: "#2FD5C8",
        aquaDim: "#1B8A80",
        amber: "#F2A93B",
        coral: "#F2603B",
        paper: "#EAF6F6",
        slate: "#7FA8AC",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
        body: ["'Inter'", "sans-serif"],
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(47,213,200,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(47,213,200,0.06) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "24px 24px",
      },
      keyframes: {
        ripple: {
          "0%": { transform: "scale(0.9)", opacity: "0.6" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
        dash: {
          to: { strokeDashoffset: "0" },
        },
      },
      animation: {
        ripple: "ripple 2.4s ease-out infinite",
        dash: "dash 1.2s ease-out forwards",
      },
    },
  },
  plugins: [],
};
