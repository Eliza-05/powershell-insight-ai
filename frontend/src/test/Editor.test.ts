import { describe, expect, it } from 'vitest'
import { textareaOffset, utf8Bytes } from '../components/Editor'

describe('Codificación y coordenadas del editor', () => {
  it('counts the same UTF-8 bytes as the backend rather than JavaScript characters', () => {
    expect(utf8Bytes('á🧪')).toBe(6)
  })
  it('maps Python code-point spans to textarea UTF-16 offsets without changing the source', () => {
    const source = '# 🧪🧪\r\nGet-Process\r\n'
    // Six Python code points precede the operation; the DOM normalizes CRLF to LF.
    const domText = '# 🧪🧪\nGet-Process\n'
    const start = textareaOffset(source, 6), end = textareaOffset(source, 17)
    expect(start).toBe(7)
    expect(domText.slice(start, end)).toBe('Get-Process')
    expect(source).toContain('\r\n')
  })
  it('preserves ASCII spans and accounts for non-BMP text before a finding', () => {
    expect(textareaOffset('a\nGet-Process', 2)).toBe(2)
    expect(textareaOffset('# 🧪\nGet-Process', 4)).toBe(5)
  })
})
