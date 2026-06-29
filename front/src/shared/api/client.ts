import type { AnswerResult, Difficulty, DifficultyOption, GenerateQuizRequest, QuizQuestion } from '../../entities/quiz/types'
import type { PokemonSpecies, UserTeam } from '../../entities/team/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

function requestQuizQuestions(payload: Required<GenerateQuizRequest>) {
  return request<{ questions: QuizQuestion[] }>('/api/v1/quiz/questions', {
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
  generateQuestions: (input: Difficulty | GenerateQuizRequest) => {
    const request = typeof input === 'string'
      ? { difficulty: input, count: 5, teamName: 'main' }
      : { count: 5, teamName: 'main', ...input }
    return requestQuizQuestions(request)
  },
  answerQuestion: (questionId: string, answer: boolean) =>
    request<AnswerResult>('/api/v1/quiz/answers', {
      method: 'POST',
      body: JSON.stringify({ questionId, answer }),
    }),
}
