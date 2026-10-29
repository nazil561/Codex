/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: '#0a0a0f', card: '#101018', elevated: '#171720', hover: '#1e1e2a' },
        fg: { DEFAULT: '#f5f5f7', muted: '#a1a1b0', dim: '#66667a' },
        accent: { DEFAULT: '#9146ff', hover: '#a970ff', soft: 'rgba(145,70,255,0.12)' },
        ok: '#3fb950',
        bad: '#f85149',
        warn: '#e3b341',
      },
      borderRadius: { card: '16px', pill: '999px' },
      fontFamily: {
        sans: ['"Inter Variable"', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"Instrument Serif"', 'Georgia', 'serif'],
      },
      boxShadow: {
        card: '0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 32px -12px rgba(0,0,0,0.5)',
        'card-hover': '0 1px 0 0 rgba(255,255,255,0.06) inset, 0 16px 48px -16px rgba(145,70,255,0.25)',
        'accent-glow': '0 0 32px -8px rgba(145,70,255,0.5)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.6', transform: 'scale(0.9)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.6s cubic-bezier(0.16,1,0.3,1) both',
        'fade-in': 'fade-in 0.5s ease-out both',
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
    },
  },
  plugins: [],
}
