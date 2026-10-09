/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0284c7',
          600: '#026597',
          700: '#034a70',
          800: '#073955',
          900: '#0c3047',
        }
      }
    },
  },
  plugins: [],
}
