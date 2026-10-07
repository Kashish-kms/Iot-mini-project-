/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#070B14',
        surface: {
          DEFAULT: '#0D1527',
          card: 'rgba(15, 23, 42, 0.75)',
          border: 'rgba(255, 255, 255, 0.08)',
          hover: 'rgba(30, 41, 59, 0.8)',
        },
        cyan: {
          neon: '#22D3EE',
          glow: 'rgba(34, 211, 238, 0.25)',
        },
        violet: {
          neon: '#8B5CF6',
          glow: 'rgba(139, 92, 246, 0.25)',
        },
        risk: {
          safe: '#10B981',
          moderate: '#F59E0B',
          high: '#F43F5E',
        }
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'sans-serif'],
        display: ['var(--font-space)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'aurora': 'aurora 15s ease infinite alternate',
        'packet-flow': 'packet 3s linear infinite',
      },
      keyframes: {
        aurora: {
          '0%': { transform: 'scale(1) rotate(0deg)' },
          '100%': { transform: 'scale(1.2) rotate(15deg)' },
        },
        packet: {
          '0%': { transform: 'translateX(0)', opacity: '0.2' },
          '50%': { opacity: '1' },
          '100%': { transform: 'translateX(100%)', opacity: '0.2' },
        }
      }
    },
  },
  plugins: [],
};
