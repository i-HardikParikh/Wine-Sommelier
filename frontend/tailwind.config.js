/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        wine: {
          50:  '#fdf2f4',
          100: '#fce7ea',
          200: '#f9d0d8',
          300: '#f4aab8',
          400: '#ec7590',
          500: '#e04a6e',
          600: '#cc2952',
          700: '#ab1e42',
          800: '#8f1c3c',
          900: '#7a1b38',
          950: '#430a1a',
        },
        burgundy: {
          DEFAULT: '#722F37',
          dark: '#4a1a20',
          light: '#9b4a55',
        },
        cream: '#F5F0E8',
        gold: '#C9A84C',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        body: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'wine-gradient': 'linear-gradient(135deg, #722F37 0%, #430a1a 50%, #1a0508 100%)',
        'gold-gradient': 'linear-gradient(135deg, #C9A84C 0%, #e8c96a 50%, #C9A84C 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'shimmer': 'shimmer 1.5s infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(12px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
      },
    },
  },
  plugins: [],
}
