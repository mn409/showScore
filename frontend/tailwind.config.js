/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0e14",
        surface: "#11161f",
        surface2: "#171d29",
        border: "#232b3a",
        neon: {
          green: "#39ff88",
          cyan: "#22d3ee",
          pink: "#ff3d81",
          yellow: "#f5d90a",
        },
        muted: "#7d8797",
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
      },
      boxShadow: {
        neon: "0 0 20px rgba(57,255,136,0.35)",
        neonCyan: "0 0 20px rgba(34,211,238,0.35)",
      },
    },
  },
  plugins: [],
};
