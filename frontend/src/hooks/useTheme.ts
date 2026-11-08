import { useEffect, useState } from 'react'
export type Theme = 'dark' | 'light'
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    try { const saved = localStorage.getItem('psi-theme'); if (saved === 'light' || saved === 'dark') return saved } catch { /* browser storage can be disabled */ }
    return 'light' // light is the product default; dark stays available as an explicit choice
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('psi-theme', theme) } catch { /* preference is still effective this session */ }
  }, [theme])
  return { theme, toggle: () => setTheme(t => t === 'dark' ? 'light' : 'dark') }
}
