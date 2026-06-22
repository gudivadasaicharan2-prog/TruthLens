/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0B1120',
          800: '#151E32',
          700: '#1E2D4D',
        },
        cyan: {
          400: '#00D4FF',
          500: '#00B8E6',
        },
        danger: '#FF4757',
        success: '#2ED573',
        warning: '#FFA502',
        text: {
          primary: '#F0F4FF',
          secondary: '#A0AEC0',
        }
      },
      fontFamily: {
        heading: ['Space Grotesk', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
      },
      backgroundImage: {
        'hex-pattern': "url('data:image/svg+xml,%3Csvg width=\"60\" height=\"60\" viewBox=\"0 0 60 60\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cpath d=\"M30 0l30 17.32v34.64L30 60 0 51.96V17.32z\" fill=\"none\" stroke=\"%2300D4FF\" stroke-opacity=\"0.05\"/%3E%3C/svg%3E')",
      },
    },
  },
  plugins: [],
}
