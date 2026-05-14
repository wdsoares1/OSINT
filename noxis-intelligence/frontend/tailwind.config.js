/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        noxis: {
          blue: '#2563eb',
          dark: '#1c2025',
          darker: '#0a0e13',
          accent: '#3b82f6',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
