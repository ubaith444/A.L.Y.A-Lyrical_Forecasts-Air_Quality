import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: "#FAFAF7",
          subtle: "#F4F2EB",
        },
        ink: {
          primary: "#25313B",
          secondary: "#687580",
          muted: "#94A3B8",
        },
        border: {
          subtle: "#E5E8E8",
          strong: "#CBD5E1",
        },
        brand: {
          aqua: "#3CD7D0",
          aquaLight: "#E6FAF9",
          aquaHover: "#22BDB6",
          deepTeal: "#0A5C59",
          sky: "#0284C7",
          skyLight: "#DCEAF4",
          mist: "#B9D1E5",
          peach: "#F5D8C8",
          sage: "#DCE7D8",
          lavender: "#E5DCEF",
        },
        cpcb: {
          good: "#16A34A",
          satisfactory: "#65A30D",
          moderate: "#CA8A04",
          poor: "#EA580C",
          veryPoor: "#DC2626",
          severe: "#7F1D1D",
        },
      },
      fontFamily: {
        sans: ["var(--font-jakarta)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02)",
        hover: "0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.02)",
        glass: "0 8px 32px 0 rgba(31, 38, 135, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
