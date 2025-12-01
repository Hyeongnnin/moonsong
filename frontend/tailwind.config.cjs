/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'Pretendard',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'Noto Sans KR',
          'sans-serif',
        ],
      },
    },
    colors: {
      // keep default gray/white/black by referencing Tailwind defaults where needed
      transparent: 'transparent',
      current: 'currentColor',
      black: '#000',
      white: '#fff',
      gray: require('tailwindcss/colors').gray,

      // Overriding the `blue` key so existing `blue-*` classes adopt the new brand (orange-brick)
      blue: {
        50:  '#fff7f5',
        100: '#fdeee9',
        200: '#fbd4c6',
        300: '#f7a88b',
        400: '#f0744c',
        500: '#e0603f',
        600: '#DE5D35', // primary brand (requested)
        700: '#C64F2C', // primary-hover approx
        800: '#9b361f',
        900: '#6e2416',
      },

      // Named alias `brand` for clarity
      brand: {
        50:  '#fff7f5',
        100: '#fdeee9',
        200: '#fbd4c6',
        300: '#f7a88b',
        400: '#f0744c',
        500: '#e0603f',
        600: '#DE5D35',
        700: '#C64F2C',
        800: '#9b361f',
        900: '#6e2416',
      },

      // keep other common Tailwind palettes available
      red: require('tailwindcss/colors').red,
      yellow: require('tailwindcss/colors').amber,
      green: require('tailwindcss/colors').emerald,
      indigo: require('tailwindcss/colors').indigo,
      purple: require('tailwindcss/colors').violet,
    },
  },
  plugins: [],
};
