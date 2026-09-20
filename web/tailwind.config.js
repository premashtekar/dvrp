# tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx,html}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B0F0A',
        fg: '#F2FFE9',
        lime: '#B4FF39',
        mint: '#39FF88',
        danger: '#FF5C5C',
      },
    },
  },
  plugins: [],
};
