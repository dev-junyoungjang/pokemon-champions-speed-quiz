import type { AnswerResult, Difficulty, DifficultyOption, QuizQuestion } from '../../entities/quiz/types'
import type { UserTeam } from '../../entities/team/types'

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

export const api = {
  getTeam: () => request<UserTeam>('/api/v1/teams/me'),
  saveTeam: (team: UserTeam) =>
    request<UserTeam>('/api/v1/teams/me', { method: 'PUT', body: JSON.stringify(team) }),
  getDifficulties: () => request<DifficultyOption[]>('/api/v1/difficulties'),
  generateQuestions: (difficulty: Difficulty) =>
    request<{ questions: QuizQuestion[] }>('/api/v1/quiz/questions', {
      method: 'POST',
      body: JSON.stringify({ difficulty, count: 5, teamName: 'main' }),
    }),
  answerQuestion: (questionId: string, answer: boolean) =>
    request<AnswerResult>('/api/v1/quiz/answers', {
      method: 'POST',
      body: JSON.stringify({ questionId, answer }),
    }),
}
