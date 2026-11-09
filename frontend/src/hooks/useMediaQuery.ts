import { useEffect, useState } from 'react'

/** Layout-only media query (e.g. where the 1A trace is placed). Never used to decide analysis behaviour. */
export function useMediaQuery(query: string) {
  const read = () => typeof window !== 'undefined' && !!window.matchMedia?.(query).matches
  const [matches, setMatches] = useState(read)
  useEffect(() => {
    const list = window.matchMedia?.(query)
    if (!list) return
    const update = () => setMatches(list.matches)
    update()
    list.addEventListener?.('change', update)
    return () => list.removeEventListener?.('change', update)
  }, [query])
  return matches
}
