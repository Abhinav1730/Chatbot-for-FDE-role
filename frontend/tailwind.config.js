/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0C1210",
        cream: "#F4EFE4",
        champagne: "#C4A574",
        forest: "#1F3D32",
        stone: "#E8E0D4",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
      },
    },
  },
  plugins: [],
};
