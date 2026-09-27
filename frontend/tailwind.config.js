/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        panel: '#0b1220',
        accent: '#67e8f9',
        good: '#34d399',
        warn: '#fbbf24',
        alert: '#f97316',
        danger: '#ef4444',
      },
    },
  },
  plugins: [],
};
