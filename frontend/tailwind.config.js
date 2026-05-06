/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
        display: ['Syne', 'sans-serif'],
      },
      colors: {
        ink: {
          950: '#09090f',
          900: '#0f0f1a',
          800: '#16162a',
          700: '#1e1e35',
          600: '#2a2a45',
          500: '#3d3d62',
          400: '#6060a0',
          300: '#9090c0',
          200: '#c0c0e0',
          100: '#e8e8f5',
          50: '#f4f4fb',
        },
        brand: '#6c63ff',
        'brand-dim': '#6c63ff22',
        'brand-mid': '#6c63ff55',
        success: '#22d3a0',
        'success-dim': '#22d3a015',
        danger: '#ff4d6d',
        'danger-dim': '#ff4d6d15',
        warn: '#ffb830',
        'warn-dim': '#ffb83015',
        info: '#38bdf8',
        'info-dim': '#38bdf815',
      },
      animation: {
        'fade-up': 'fadeUp 0.4s ease-out forwards',
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'slide-right': 'slideRight 0.3s ease-out forwards',
        'scale-in': 'scaleIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'progress': 'progress 1.5s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideRight: {
          '0%': { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.85)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        progress: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(400%)' },
        },
      },
    },
  },
  plugins: [],
}
