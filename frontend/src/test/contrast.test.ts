import { expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

// Read the actual stylesheet so a CSS regression cannot pass against copied colours.
const tokens = readFileSync('src/styles/tokens.css', 'utf8')
const css = readFileSync('src/styles/studio.css', 'utf8')
const [light, dark] = tokens.split(":root[data-theme='dark']")
const declarations = (text: string) => Object.fromEntries([...text.matchAll(/(--[\w-]+):\s*(#[\da-f]{6})\s*;/gi)].map(m => [m[1], m[2]]))
const rule = (selector: string) => {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = css.match(new RegExp(escaped + '\\s*\\{([^}]+)\\}'))
  expect(match, `Missing CSS rule ${selector}`).not.toBeNull()
  return match![1]
}
const property = (rule: string, name: string) => rule.match(new RegExp(`(?:^|;)\\s*${name}:\\s*([^;]+)`))![1].trim()
const rgb = (hex: string) => [1, 3, 5].map(i => Number.parseInt(hex.slice(i, i + 2), 16))
const luminance = (rgb: number[]) => rgb.map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((n, v, i) => n + v * [.2126, .7152, .0722][i], 0)
const contrast = (a: number[], b: number[]) => (Math.max(luminance(a), luminance(b)) + .05) / (Math.min(luminance(a), luminance(b)) + .05)

it.each(['light', 'dark'])('H04: selected A/B/C text and primary hover exceed 4.5:1 in %s', theme => {
  const colors = { ...declarations(light), ...(theme === 'dark' ? declarations(dark) : {}) }
  const resolve = (value: string) => rgb(colors[value.match(/^var\((--[\w-]+)\)$/)![1]])
  const selected = rule('.pipeline-option.selected .pipeline-key')
  expect(contrast(resolve(property(selected, 'color')), resolve(property(selected, 'background')))).toBeGreaterThanOrEqual(4.5)
  const primary = rule('.button.primary'), hover = rule('.button.primary:hover:not(:disabled)')
  const brightness = Number(property(hover, 'filter').match(/^brightness\(([.\d]+)\)$/)![1])
  const filtered = (value: string) => resolve(value).map(channel => Math.min(255, channel * brightness))
  expect(contrast(filtered(property(primary, 'color')), filtered(property(primary, 'background')))).toBeGreaterThanOrEqual(4.5)
})
