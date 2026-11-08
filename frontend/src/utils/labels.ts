/** Spanish display names for fixed backend values. Display only: the data, its codes and the exported JSON are unchanged.
 *  Free-text backend messages (reasons, warnings, limitations) are NOT translated; the UI shows them as technical detail. */

export const recoveryKindNames: Record<string, string> = {
  script_text: 'texto de script', string: 'cadena', bytes: 'bytes',
  variable_definition: 'definición de variable', variable_use: 'uso de variable', unresolved: 'sin resolver',
}

export const stepStatusNames: Record<string, string> = {
  success: 'recuperada', partial: 'bytes parciales', failed: 'fallida', unsupported: 'no soportada',
}

export const techniqueNames: Record<string, string> = {
  'OT-B64-ENCCMD': 'Base64 (-EncodedCommand)', 'OT-B64-INLINE': 'Base64 en línea', 'OT-CONCAT': 'Concatenación',
  'OT-VARSUB': 'Sustitución de variable', 'OT-FORMAT': 'Operador de formato (-f)', 'OT-OTHER': 'Otra técnica',
}

/** "Concatenación · OT-CONCAT"; unknown codes are shown as they arrive. */
export function techniqueLabel(code: string) { return techniqueNames[code] ? `${techniqueNames[code]} · ${code}` : code }
export const recoveryKindLabel = (kind: string) => recoveryKindNames[kind] ?? kind
export const stepStatusLabel = (status: string) => stepStatusNames[status] ?? status

/** Spanish number formatting for durations: 0.0123 → "0,01 s". */
export function formatSeconds(value: number, digits = 2) {
  return `${value.toLocaleString('es-CO', { minimumFractionDigits: digits, maximumFractionDigits: digits })} s`
}
