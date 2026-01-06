const colors = require('tailwindcss/colors')

module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './apps/**/*.html',
    './apps/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        yellow: colors.yellow,
        green: colors.green,
        purple: colors.purple,
        primary: '#13ec5b',
        'background-light': '#f6f8f6',
        'background-dark': '#102216',
      },
      fontFamily: {
        display: ['Plus Jakarta Sans', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.25rem',
        lg: '0.5rem',
        xl: '0.75rem',
        full: '9999px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
}
