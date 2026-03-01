/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Cinzel', 'serif'],
        body: ['Crimson Text', 'serif'],
      },
      colors: {
        parchment: {
          50: '#fefdfb',
          100: '#fdf8f0',
          200: '#f9edd8',
          300: '#f3ddb8',
          400: '#e8c68e',
          500: '#d4a86a',
        },
        ink: {
          700: '#2d2a26',
          800: '#1f1d1a',
          900: '#141311',
        },
        blood: {
          400: '#c45b5b',
          500: '#a13d3d',
          600: '#7e2f2f',
        },
        mystic: {
          400: '#7b68c9',
          500: '#5c4ca3',
          600: '#44387a',
        },
        forest: {
          400: '#5a9a6b',
          500: '#3d7a50',
          600: '#2d5a3b',
        },
        gold: {
          400: '#d4af37',
          500: '#b8942f',
          600: '#8a6f23',
        },
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'flicker': 'flicker 3s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(212, 175, 55, 0.3)' },
          '100%': { boxShadow: '0 0 40px rgba(212, 175, 55, 0.6)' },
        },
        flicker: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.8 },
        },
      },
    },
  },
  plugins: [],
}

