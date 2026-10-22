import { defineMermaidSetup } from '@slidev/types'

// Deck palette for the pipeline diagram (slide 3), instead of the default purple theme.
export default defineMermaidSetup(() => ({
  theme: 'base',
  themeVariables: {
    background: '#f7f6f2',
    primaryColor: '#ffffff',
    primaryBorderColor: '#0f766e',
    primaryTextColor: '#14213d',
    lineColor: '#617083',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: '17px',
  },
}))
