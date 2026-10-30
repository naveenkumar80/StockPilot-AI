/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0B0E14",
        surface: "#12161F",
        card: "#181E29",
        cardHover: "#1E2634",
        border: "#252E3E",
        borderSubtle: "#1C2432",
        textPrimary: "#F8FAFC",
        textSecondary: "#94A3B8",
        textMuted: "#64748B",
        marketGreen: "#10B981",
        marketGreenSubtle: "rgba(16, 185, 129, 0.12)",
        marketRed: "#EF4444",
        marketRedSubtle: "rgba(239, 68, 68, 0.12)",
        marketYellow: "#F59E0B",
        marketYellowSubtle: "rgba(245, 158, 11, 0.12)",
        accentBlue: "#3B82F6",
        accentBlueSubtle: "rgba(59, 130, 246, 0.12)",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "Oxygen",
          "Ubuntu",
          "Cantarell",
          "sans-serif",
        ],
        mono: [
          '"SF Mono"',
          "Menlo",
          "Monaco",
          "Consolas",
          '"Liberation Mono"',
          '"Courier New"',
          "monospace",
        ],
      },
    },
  },
  plugins: [],
}
