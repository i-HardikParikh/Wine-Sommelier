/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        wine: {
          50:  '#111827', // Darkest text
          100: '#1f2937', // Dark text
          200: '#374151',
          300: '#4b5563', // Secondary text
          400: '#6b7280', // Muted text
          500: '#9ca3af', // Border or light lines
          600: '#722F37', // Wine brand color (primary accent)
          700: '#d1d5db', // Light border
          800: '#e5e7eb', // Border / bubble bg
          900: '#f3f4f6', // Light gray bg
          950: '#faf9f6', // Main app background (soft off-white)
        },
        burgundy: {
          DEFAULT: '#722F37',
          dark: '#5c242a',
          light: '#8b3d48',
        },
        cream: '#111827', // Main text color
        gold: '#9a7b2c',   // High-contrast gold for light background
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        body: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'wine-gradient': 'linear-gradient(135deg, #faf9f6 0%, #f3f4f6 50%, #e5e7eb 100%)',
        'gold-gradient': 'linear-gradient(135deg, #9a7b2c 0%, #c9a84c 50%, #9a7b2c 100%)',
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
