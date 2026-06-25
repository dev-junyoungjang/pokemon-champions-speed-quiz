import type { TeamMember } from '../team/types'

export type Difficulty = 'easy' | 'normal' | 'hard' | 'expert' | 'master'

export type DifficultyOption = {
  id: Difficulty
  label: string
  description: string
}

export type QuizQuestion = {
  id: string
  difficulty: Difficulty
  mode: 'IS_FASTER'
  statement: string
  answerType: 'YES_NO'
  correctAnswer: boolean
  subject: {
    build: TeamMember
    speed: { rawSpeed: number; effectiveSpeed: number; modifiers: string[] }
  }
  opponent: {
    build: TeamMember
    speed: { rawSpeed: number; effectiveSpeed: number; modifiers: string[] }
  }
  explanation: string
  rulesetVersion: string
}

export type AnswerResult = {
  correct: boolean
  correctAnswer: boolean
  explanation: string
  subjectSpeed: number
  opponentSpeed: number
}
