import type { AnalysisResponse, Capabilities, Metadata, Mode, ModelStatus } from '../types/api'

export class ApiFailure extends Error {
  constructor(public code: string, message: string, public status = 0) { super(message); this.name = 'ApiFailure' }
}

async function request<T>(path: string, body?: unknown, timeout = 15000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const response = await fetch(`/api/${path}`, {
      method: body === undefined ? 'GET' : 'POST',
      ...(body === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
      cache: 'no-store', signal: controller.signal,
    })
    const data = await response.json()
    if (!response.ok) throw new ApiFailure(data.error?.code ?? 'http_error', data.error?.message ?? `Error HTTP ${response.status}`, response.status)
    return data as T
  } catch (error) {
    if (error instanceof ApiFailure) throw error
    if (typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError')
      throw new ApiFailure('connection_timeout', 'Se agotó la espera. El servidor podría seguir trabajando; consulta el estado antes de volver a analizar.')
    throw new ApiFailure('connection_error', 'No se pudo conectar con la API local. Comprueba que el backend esté iniciado.')
  } finally { clearTimeout(timer) }
}

export const api = {
  health: () => request<{ status: string; version: string }>('health'),
  capabilities: () => request<Capabilities>('capabilities'),
  metadata: () => request<Metadata>('metadata'),
  modelStatus: () => request<ModelStatus>('ollama/status'),
  analyze: (script: string, mode: Mode) => request<AnalysisResponse>(mode === 'ABC' ? 'compare' : `analyze/${mode}`, { script }, 660000),
}
