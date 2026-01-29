/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'mf-bg': '#0f0f0f',
        'mf-panel': '#1a1a1a',
        'mf-border': '#2a2a2a',
        'mf-hover': '#252525',
        'mf-accent': '#3b82f6',
        'mf-text': '#e5e5e5',
        'mf-muted': '#888888',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
