import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#15211d",
        canvas: "#f4f7f4",
        panel: "#ffffff",
        accent: "#157b63",
        accentdark: "#0e5d4a",
        line: "#dbe5df",
      },
      boxShadow: {
        panel: "0 8px 24px rgba(21, 33, 29, 0.07)",
      },
    },
  },
  plugins: [],
} satisfies Config;
