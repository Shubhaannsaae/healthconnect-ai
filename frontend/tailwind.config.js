/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
      './src/components/**/*.{js,ts,jsx,tsx,mdx}',
      './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          // Primary brand colors
          primary: {
            50: '#f0f9ff',
            100: '#e0f2fe',
            200: '#bae6fd',
            300: '#7dd3fc',
            400: '#38bdf8',
            500: '#0ea5e9',
            600: '#0284c7',
            700: '#0369a1',
            800: '#075985',
            900: '#0c4a6e',
            950: '#082f49',
          },
          // Secondary colors for healthcare
          secondary: {
            50: '#f8fafc',
            100: '#f1f5f9',
            200: '#e2e8f0',
            300: '#cbd5e1',
            400: '#94a3b8',
            500: '#64748b',
            600: '#475569',
            700: '#334155',
            800: '#1e293b',
            900: '#0f172a',
            950: '#020617',
          },
          // Success colors for positive health indicators
          success: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
            950: '#052e16',
          },
          // Warning colors for concerning health data
          warning: {
            50: '#fffbeb',
            100: '#fef3c7',
            200: '#fde68a',
            300: '#fcd34d',
            400: '#fbbf24',
            500: '#f59e0b',
            600: '#d97706',
            700: '#b45309',
            800: '#92400e',
            900: '#78350f',
            950: '#451a03',
          },
          // Danger colors for critical health alerts
          danger: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            300: '#fca5a5',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
            800: '#991b1b',
            900: '#7f1d1d',
            950: '#450a0a',
          },
          // Healthcare specific colors
          health: {
            heart: '#e74c3c',
            blood: '#c0392b',
            oxygen: '#3498db',
            glucose: '#f39c12',
            temperature: '#e67e22',
            pressure: '#9b59b6',
            pulse: '#e91e63',
            respiratory: '#00bcd4',
          }
        },
        fontFamily: {
          sans: ['Inter', 'system-ui', 'sans-serif'],
          mono: ['JetBrains Mono', 'Consolas', 'monospace'],
          medical: ['Source Sans Pro', 'system-ui', 'sans-serif'],
        },
        fontSize: {
          '2xs': ['0.625rem', { lineHeight: '0.75rem' }],
          '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
          '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
          '5xl': ['3rem', { lineHeight: '1' }],
          '6xl': ['3.75rem', { lineHeight: '1' }],
          '7xl': ['4.5rem', { lineHeight: '1' }],
          '8xl': ['6rem', { lineHeight: '1' }],
          '9xl': ['8rem', { lineHeight: '1' }],
        },
        spacing: {
          '18': '4.5rem',
          '88': '22rem',
          '128': '32rem',
          '144': '36rem',
        },
        maxWidth: {
          '8xl': '88rem',
          '9xl': '96rem',
        },
        borderRadius: {
          '4xl': '2rem',
          '5xl': '2.5rem',
        },
        boxShadow: {
          'health': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          'health-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          'health-xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          'inner-health': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
          'glow': '0 0 20px rgba(59, 130, 246, 0.5)',
          'glow-green': '0 0 20px rgba(34, 197, 94, 0.5)',
          'glow-red': '0 0 20px rgba(239, 68, 68, 0.5)',
          'glow-yellow': '0 0 20px rgba(245, 158, 11, 0.5)',
        },
        animation: {
          'fade-in': 'fadeIn 0.5s ease-in-out',
          'fade-out': 'fadeOut 0.5s ease-in-out',
          'slide-in': 'slideIn 0.3s ease-out',
          'slide-out': 'slideOut 0.3s ease-in',
          'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
          'bounce-slow': 'bounce 2s infinite',
          'heartbeat': 'heartbeat 1.5s ease-in-out infinite',
          'breathing': 'breathing 4s ease-in-out infinite',
          'float': 'float 3s ease-in-out infinite',
          'glow': 'glow 2s ease-in-out infinite alternate',
        },
        keyframes: {
          fadeIn: {
            '0%': { opacity: '0' },
            '100%': { opacity: '1' },
          },
          fadeOut: {
            '0%': { opacity: '1' },
            '100%': { opacity: '0' },
          },
          slideIn: {
            '0%': { transform: 'translateX(-100%)' },
            '100%': { transform: 'translateX(0)' },
          },
          slideOut: {
            '0%': { transform: 'translateX(0)' },
            '100%': { transform: 'translateX(-100%)' },
          },
          heartbeat: {
            '0%, 100%': { transform: 'scale(1)' },
            '50%': { transform: 'scale(1.1)' },
          },
          breathing: {
            '0%, 100%': { transform: 'scale(1)' },
            '50%': { transform: 'scale(1.05)' },
          },
          float: {
            '0%, 100%': { transform: 'translateY(0px)' },
            '50%': { transform: 'translateY(-10px)' },
          },
          glow: {
            '0%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.5)' },
            '100%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.8)' },
          },
        },
        backdropBlur: {
          xs: '2px',
        },
        screens: {
          'xs': '475px',
          '3xl': '1600px',
        },
      },
    },
    plugins: [
      require('@tailwindcss/forms'),
      require('@tailwindcss/typography'),
      function({ addUtilities, addComponents, theme }) {
        // Custom utilities for healthcare UI
        addUtilities({
          '.text-gradient': {
            'background': 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
            '-webkit-background-clip': 'text',
            '-webkit-text-fill-color': 'transparent',
            'background-clip': 'text',
          },
          '.bg-gradient-health': {
            'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          },
          '.bg-gradient-success': {
            'background': 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
          },
          '.bg-gradient-warning': {
            'background': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
          },
          '.bg-gradient-danger': {
            'background': 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
          },
          '.scrollbar-hide': {
            '-ms-overflow-style': 'none',
            'scrollbar-width': 'none',
            '&::-webkit-scrollbar': {
              display: 'none',
            },
          },
          '.scrollbar-thin': {
            'scrollbar-width': 'thin',
            '&::-webkit-scrollbar': {
              width: '6px',
            },
            '&::-webkit-scrollbar-track': {
              background: theme('colors.gray.100'),
            },
            '&::-webkit-scrollbar-thumb': {
              background: theme('colors.gray.300'),
              'border-radius': '3px',
            },
            '&::-webkit-scrollbar-thumb:hover': {
              background: theme('colors.gray.400'),
            },
          },
        });
  
        // Custom components for healthcare UI
        addComponents({
          '.health-card': {
            'background': 'white',
            'border-radius': theme('borderRadius.xl'),
            'box-shadow': theme('boxShadow.health'),
            'border': `1px solid ${theme('colors.gray.200')}`,
            'padding': theme('spacing.6'),
            'transition': 'all 0.2s ease-in-out',
            '&:hover': {
              'box-shadow': theme('boxShadow.health-lg'),
              'transform': 'translateY(-2px)',
            },
          },
          '.health-button': {
            'display': 'inline-flex',
            'align-items': 'center',
            'justify-content': 'center',
            'border-radius': theme('borderRadius.lg'),
            'font-weight': theme('fontWeight.medium'),
            'transition': 'all 0.2s ease-in-out',
            'cursor': 'pointer',
            'border': 'none',
            'outline': 'none',
            '&:focus': {
              'box-shadow': `0 0 0 3px ${theme('colors.primary.200')}`,
            },
            '&:disabled': {
              'opacity': '0.5',
              'cursor': 'not-allowed',
            },
          },
          '.health-input': {
            'width': '100%',
            'border-radius': theme('borderRadius.lg'),
            'border': `1px solid ${theme('colors.gray.300')}`,
            'padding': `${theme('spacing.3')} ${theme('spacing.4')}`,
            'font-size': theme('fontSize.sm'),
            'transition': 'all 0.2s ease-in-out',
            '&:focus': {
              'border-color': theme('colors.primary.500'),
              'box-shadow': `0 0 0 3px ${theme('colors.primary.200')}`,
              'outline': 'none',
            },
            '&::placeholder': {
              'color': theme('colors.gray.400'),
            },
          },
          '.health-badge': {
            'display': 'inline-flex',
            'align-items': 'center',
            'padding': `${theme('spacing.1')} ${theme('spacing.3')}`,
            'border-radius': theme('borderRadius.full'),
            'font-size': theme('fontSize.xs'),
            'font-weight': theme('fontWeight.medium'),
            'text-transform': 'uppercase',
            'letter-spacing': theme('letterSpacing.wide'),
          },
        });
      },
    ],
  };
  