import type { Mode, ModelStatus } from '../types/api'
import { analysisResponse, capabilitiesResponse, healthResponse, httpError, metadataResponse, modelStatusResponse } from './contracts'

export class ApiFailure extends Error {
  constructor(public code: string, message: string, public status = 0) { super(message); this.name = 'ApiFailure' }
}

function transportFailure(error: unknown): ApiFailure {
  return typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError'
    ? new ApiFailure('connection_timeout', 'Se agotó la espera. El servidor podría seguir trabajando; consulta el estado antes de volver a analizar.')
    : new ApiFailure('connection_error', 'No se pudo conectar con la API local. Comprueba que el backend esté iniciado.')
}

async function request<T>(path: string, decode: (value: unknown) => T | Promise<T>, body?: unknown, timeout = 15000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    let response: Response
    try {
      response = await fetch(`/api/${path}`, {
        method: body === undefined ? 'GET' : 'POST',
        ...(body === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
        cache: 'no-store', signal: controller.signal,
      })
    } catch (error) { throw transportFailure(error) }
    let data: unknown
    try { data = await response.json() }
    catch (error) {
      if (!response.ok) throw new ApiFailure('http_error', `Error HTTP ${response.status}. El servidor no devolvió un error JSON válido. Puedes volver a intentarlo.`, response.status)
      if (typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError') throw transportFailure(error)
      throw new ApiFailure('invalid_json', 'La API devolvió JSON inválido. No se aceptaron resultados. Puedes volver a analizar.', response.status)
    }
    if (!response.ok) {
      const error = httpError(data)
      throw new ApiFailure(error?.code ?? 'http_error', error?.message ?? `Error HTTP ${response.status}. La solicitud no pudo completarse.`, response.status)
    }
    try { return await decode(data) }
    catch { throw new ApiFailure('invalid_contract', 'La respuesta de la API no cumple el contrato esperado. No se aceptaron resultados. Puedes volver a analizar.', response.status) }
  } finally { clearTimeout(timer) }
}

// StrictMode and overlapping refreshes share only the in-flight provider poll.
// No cached state or retry survives settlement; FastAPI admits one status poll at a time.
let pendingModelStatus: Promise<ModelStatus> | undefined
function modelStatus() {
  pendingModelStatus ??= request('ollama/status', modelStatusResponse).finally(() => { pendingModelStatus = undefined })
  return pendingModelStatus
}

export const api = {
  health: () => request('health', healthResponse),
  capabilities: () => request('capabilities', capabilitiesResponse),
  metadata: () => request('metadata', metadataResponse),
  modelStatus,
  analyze: (script: string, mode: Mode) => request(mode === 'ABC' ? 'compare' : `analyze/${mode}`, value => analysisResponse(value, mode, script), { script }, 660000),
}
