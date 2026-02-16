import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef7ff",
          100: "#daecff",
          200: "#badbff",
          500: "#0f6bcf",
          700: "#0a4a91"
        },
        ink: "#122026",
        sand: "#fbf8f1",
        accent: "#f97316"
      },
      borderRadius: {
        xl: "1rem"
      },
      boxShadow: {
        soft: "0 10px 25px -15px rgba(15, 107, 207, 0.45)"
      }
    }
  },
  plugins: []
};

export default config;
