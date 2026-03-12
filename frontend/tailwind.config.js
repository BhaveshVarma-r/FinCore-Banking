module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        fincore: {
          50: "#f0f4ff", 100: "#e0e9ff", 200: "#c7d7fe",
          300: "#a5bbfc", 400: "#8194f8", 500: "#6366f1",
          600: "#4f46e5", 700: "#4338ca", 800: "#3730a3",
          900: "#312e81", 950: "#1e1b4b",
        },
      },
      animation: {
        "slide-in": "slideIn 0.3s ease-out",
      },
      keyframes: {
        slideIn: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
}