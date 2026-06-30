import type { AnswerResult, Difficulty, DifficultyOption, GenerateQuizRequest, GenerateQuizResponse } from '../../entities/quiz/types'
import type { HeldItemOption, PokemonSpecies, UserTeam } from '../../entities/team/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const USER_SESSION_STORAGE_KEY = 'pokemon-champions:user-session-id'

function createUserSessionId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `session-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
}

function getUserSessionId() {
  const storage = globalThis.localStorage
  const legacySessionStorage = globalThis.sessionStorage
  const existing = storage?.getItem(USER_SESSION_STORAGE_KEY)
  if (existing) return existing

  const legacySessionId = legacySessionStorage?.getItem(USER_SESSION_STORAGE_KEY)
  if (legacySessionId) {
    storage?.setItem(USER_SESSION_STORAGE_KEY, legacySessionId)
    return legacySessionId
  }

  const created = createUserSessionId()
  storage?.setItem(USER_SESSION_STORAGE_KEY, created)
  return created
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      'X-User-Session-Id': getUserSessionId(),
      ...options?.headers,
    },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

function requestQuizQuestions(payload: Required<GenerateQuizRequest>) {
  return request<GenerateQuizResponse>('/api/v1/quiz/questions', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export const api = {
  getTeam: () => request<UserTeam>('/api/v1/teams/me'),
  saveTeam: (team: UserTeam) =>
    request<UserTeam>('/api/v1/teams/me', { method: 'PUT', body: JSON.stringify(team) }),
  getDifficulties: () => request<DifficultyOption[]>('/api/v1/difficulties'),
  getPokemonSpecies: (query: string) => request<{ species: PokemonSpecies }>(`/api/v1/pokemon/species?query=${encodeURIComponent(query)}`),
  getHeldItems: () => request<{ items: HeldItemOption[] }>('/api/v1/items'),
  generateQuestions: (input: Difficulty | GenerateQuizRequest) => {
    const request = typeof input === 'string'
      ? { difficulty: input, count: 5, teamName: 'main' }
      : { count: 5, teamName: 'main', ...input }
    return requestQuizQuestions(request)
  },
  answerQuestion: (questionId: string, answer: boolean, sessionId?: string | null) =>
    request<AnswerResult>('/api/v1/quiz/answers', {
      method: 'POST',
      body: JSON.stringify({ questionId, answer, sessionId }),
    }),
}
