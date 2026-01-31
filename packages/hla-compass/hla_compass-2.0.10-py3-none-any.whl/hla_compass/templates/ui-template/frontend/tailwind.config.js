/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./*.{js,ts,jsx,tsx}",
    "./**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'mono': ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Consolas', 'Liberation Mono', 'Menlo', 'monospace'],
        'sans': ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#f1f0ff',
          100: '#dcd9fb',
          200: '#bebbf5',
          300: '#a19cf0',
          400: '#857ee9',
          500: '#827DD3',
          600: '#6c66b4',
          700: '#565093',
          800: '#403a72',
          900: '#2b264f',
        },
        // Scientific data colors - optimized for accessibility
        data: {
          primary: '#827DD3',    // Brand primary
          secondary: '#06b6d4',  // Cyan for secondary data
          accent: '#10b981',     // Green for positive/confirmation
          warning: '#f59e0b',    // Amber for warnings
          danger: '#ef4444',     // Red for errors/danger
          info: '#3b82f6',       // Blue for information
          neutral: '#737373',    // Gray for neutral states
        },
        // Chart colors - scientifically chosen for distinguishability
        chart: {
          blue: '#3b82f6',
          teal: '#06b6d4',
          green: '#10b981',
          orange: '#f97316',
          purple: '#8b5cf6',
          pink: '#ec4899',
          indigo: '#6366f1',
          cyan: '#06b6d4',
          lime: '#84cc16',
          gray: '#737373',
          amber: '#f59e0b',
          red: '#ef4444',
          violet: '#8b5cf6',
        },
        // Surface colors for scientific interfaces
        surface: {
          primary: '#ffffff',
          secondary: '#fafafa',
          tertiary: '#f5f5f5',
          elevated: '#ffffff',
        },
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0, 0, 0, 0.05)',
        'medium': '0 4px 16px rgba(0, 0, 0, 0.1)',
        'strong': '0 8px 32px rgba(0, 0, 0, 0.15)',
        'chart': '0 2px 8px rgba(0, 0, 0, 0.08)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.25rem',
        '3xl': '1.5rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
  // Important for Ant Design compatibility
  corePlugins: {
    preflight: false,
  },
  // Performance optimizations
  future: {
    hoverOnlyWhenSupported: true,
  },
}
