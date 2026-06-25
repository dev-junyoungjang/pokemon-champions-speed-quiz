import { QueryClient, QueryClientProvider, useMutation, useQuery } from '@tanstack/react-query'
import styled from '@emotion/styled'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { api } from '../shared/api/client'
import { Button, ContentFrame, Input, PageShell, Panel, SmallText } from '../shared/ui/primitives'
import { theme } from '../shared/styles/theme'
import type { Difficulty, QuizQuestion } from '../entities/quiz/types'
import type { TeamMember, UserTeam } from '../entities/team/types'

const queryClient = new QueryClient()

const Header = styled.header`
  display: grid;
  gap: 12px;
  margin-bottom: 24px;
`

const Eyebrow = styled.span`
  color: ${theme.color.primaryDark};
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
`

const Title = styled.h1`
  max-width: 760px;
  margin: 0;
  font-size: clamp(36px, 7vw, 72px);
  line-height: 0.95;
`

const Layout = styled.div`
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 20px;

  @media (max-width: 860px) {
    grid-template-columns: 1fr;
  }
`

const TeamGrid = styled.div`
  display: grid;
  gap: 12px;
`

const SlotCard = styled.div`
  display: grid;
  gap: 12px;
  border: 1px solid ${theme.color.line};
  border-radius: 18px;
  background: white;
  padding: 14px;
`

const FieldGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;

  @media (max-width: 620px) {
    grid-template-columns: 1fr;
  }
`

const DifficultyList = styled.div`
  display: grid;
  gap: 10px;
`

const QuizStage = styled.div`
  display: grid;
  min-height: 420px;
  place-items: center;
`

const SwipeCard = styled(motion.div)`
  width: min(460px, 100%);
  min-height: 330px;
  display: grid;
  align-content: space-between;
  border-radius: 32px;
  background: linear-gradient(145deg, #fffdf8, #fff0ca);
  border: 1px solid ${theme.color.line};
  box-shadow: ${theme.shadow.card};
  padding: 28px;
  touch-action: pan-y;
`

const BigStatement = styled.h2`
  margin: 0;
  font-size: clamp(26px, 6vw, 42px);
  line-height: 1.12;
`

const ActionRow = styled.div`
  display: flex;
  gap: 12px;
  justify-content: space-between;
  flex-wrap: wrap;
`

const ResultBox = styled.div<{ correct: boolean }>`
  border-radius: 18px;
  padding: 14px;
  background: ${({ correct }) => (correct ? 'rgba(39, 134, 95, 0.12)' : 'rgba(180, 61, 61, 0.12)')};
  color: ${({ correct }) => (correct ? theme.color.yes : theme.color.no)};
  font-weight: 800;
`

const defaultMember = (slot: number): TeamMember => ({
  slot,
  pokemonId: slot === 1 ? 'garchomp' : `pokemon-${slot}`,
  pokemonName: slot === 1 ? 'Garchomp' : '',
  baseStatsSnapshot: { hp: 1, atk: 1, def: 1, spa: 1, spd: 1, spe: 80 },
  level: 50,
  nature: 'Jolly',
  ability: null,
  item: null,
  evs: { spe: 252 },
  ivs: { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 },
})

function AppContent() {
  const [teamDraft, setTeamDraft] = useState<UserTeam>({
    teamName: 'main',
    format: 'pokemon_champions',
    members: Array.from({ length: 6 }, (_, index) => defaultMember(index + 1)),
  })
  const [selectedDifficulty, setSelectedDifficulty] = useState<Difficulty | null>(null)
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [questionIndex, setQuestionIndex] = useState(0)
  const [lastResult, setLastResult] = useState<string | null>(null)

  const teamQuery = useQuery({ queryKey: ['team'], queryFn: api.getTeam })
  const difficultiesQuery = useQuery({ queryKey: ['difficulties'], queryFn: api.getDifficulties })
  const saveTeam = useMutation({ mutationFn: api.saveTeam })
  const generateQuiz = useMutation({
    mutationFn: api.generateQuestions,
    onSuccess: (data) => {
      setQuestions(data.questions)
      setQuestionIndex(0)
      setLastResult(null)
    },
  })
  const answerQuestion = useMutation({ mutationFn: ({ id, answer }: { id: string; answer: boolean }) => api.answerQuestion(id, answer) })

  useEffect(() => {
    if (teamQuery.data) {
      const filledMembers = Array.from({ length: 6 }, (_, index) => teamQuery.data.members[index] ?? defaultMember(index + 1))
      setTeamDraft({ ...teamQuery.data, members: filledMembers })
    }
  }, [teamQuery.data])

  const currentQuestion = questions[questionIndex]

  function updateMember(slot: number, patch: Partial<TeamMember>) {
    setTeamDraft((team) => ({
      ...team,
      members: team.members.map((member) => (member.slot === slot ? { ...member, ...patch } : member)),
    }))
  }

  function updateBaseSpeed(slot: number, spe: number) {
    const member = teamDraft.members.find((candidate) => candidate.slot === slot)
    if (!member) return
    updateMember(slot, { baseStatsSnapshot: { ...member.baseStatsSnapshot, spe } })
  }

  async function answer(answer: boolean) {
    if (!currentQuestion) return
    const result = await answerQuestion.mutateAsync({ id: currentQuestion.id, answer })
    setLastResult(`${result.correct ? '정답!' : '오답!'} ${result.explanation}`)
    setQuestionIndex((index) => index + 1)
  }

  return (
    <PageShell>
      <ContentFrame>
        <Header>
          <Eyebrow>Pokémon Champions Speed Tier Trainer</Eyebrow>
          <Title>내 엔트리로 메타 스피드 감각을 스와이프 퀴즈처럼 훈련해요.</Title>
          <SmallText>Tailwind 없이 Emotion styled component로 구성했습니다. MVP 디자인 시스템은 직접 만든 토큰/primitive를 사용합니다.</SmallText>
        </Header>

        <Layout>
          <Panel>
            <h2>내 엔트리 6마리</h2>
            <SmallText>Game8식 파티 등록처럼 6개 슬롯을 한 화면에서 빠르게 수정하는 구조입니다. 지금은 이름, 종족값 Speed, 성격, 아이템, 특성, Speed EV부터 받습니다.</SmallText>
            <TeamGrid>
              {teamDraft.members.map((member) => (
                <SlotCard key={member.slot}>
                  <strong>Slot {member.slot}</strong>
                  <FieldGrid>
                    <label>
                      Pokémon
                      <Input value={member.pokemonName} onChange={(event) => updateMember(member.slot, { pokemonName: event.target.value, pokemonId: event.target.value.toLowerCase().replace(/\s+/g, '-') })} />
                    </label>
                    <label>
                      Base Speed
                      <Input type="number" value={member.baseStatsSnapshot.spe} onChange={(event) => updateBaseSpeed(member.slot, Number(event.target.value))} />
                    </label>
                    <label>
                      Speed EV
                      <Input type="number" value={member.evs.spe ?? 0} onChange={(event) => updateMember(member.slot, { evs: { ...member.evs, spe: Number(event.target.value) } })} />
                    </label>
                    <label>
                      Nature
                      <Input value={member.nature} onChange={(event) => updateMember(member.slot, { nature: event.target.value })} />
                    </label>
                    <label>
                      Item
                      <Input value={member.item ?? ''} onChange={(event) => updateMember(member.slot, { item: event.target.value || null })} />
                    </label>
                    <label>
                      Ability
                      <Input value={member.ability ?? ''} onChange={(event) => updateMember(member.slot, { ability: event.target.value || null })} />
                    </label>
                  </FieldGrid>
                </SlotCard>
              ))}
            </TeamGrid>
            <ActionRow style={{ marginTop: 16 }}>
              <Button onClick={() => saveTeam.mutate(teamDraft)} disabled={saveTeam.isPending}>{saveTeam.isPending ? '저장 중...' : '엔트리 저장'}</Button>
            </ActionRow>
          </Panel>

          <Panel>
            <h2>퀴즈 시작</h2>
            <SmallText>난이도를 고르면 서버가 현재 엔트리와 활성 메타 샘플을 섞어서 문제를 생성합니다.</SmallText>
            <DifficultyList>
              {difficultiesQuery.data?.map((difficulty) => (
                <Button
                  key={difficulty.id}
                  tone={selectedDifficulty === difficulty.id ? 'primary' : 'ghost'}
                  onClick={() => {
                    setSelectedDifficulty(difficulty.id)
                    generateQuiz.mutate(difficulty.id)
                  }}
                >
                  {difficulty.label} — {difficulty.description}
                </Button>
              ))}
            </DifficultyList>

            <QuizStage>
              {generateQuiz.isPending && <SmallText>문제 생성 중... 메타 샘플과 내 엔트리 스피드를 계산하고 있어요.</SmallText>}
              {!generateQuiz.isPending && currentQuestion && (
                <AnimatePresence mode="wait">
                  <SwipeCard
                    key={currentQuestion.id}
                    drag="x"
                    dragConstraints={{ left: 0, right: 0 }}
                    onDragEnd={(_, info) => {
                      if (info.offset.x > 90) void answer(true)
                      if (info.offset.x < -90) void answer(false)
                    }}
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.96 }}
                  >
                    <Eyebrow>{currentQuestion.difficulty} · 오른쪽 Yes / 왼쪽 No</Eyebrow>
                    <BigStatement>{currentQuestion.statement}</BigStatement>
                    <ActionRow>
                      <Button tone="no" onClick={() => void answer(false)}>← 틀림</Button>
                      <Button tone="yes" onClick={() => void answer(true)}>맞음 →</Button>
                    </ActionRow>
                  </SwipeCard>
                </AnimatePresence>
              )}
              {!generateQuiz.isPending && questions.length > 0 && !currentQuestion && <SmallText>이번 세트 완료! 다른 난이도로 다시 시작해보세요.</SmallText>}
            </QuizStage>
            {lastResult && <ResultBox correct={lastResult.startsWith('정답')}>{lastResult}</ResultBox>}
          </Panel>
        </Layout>
      </ContentFrame>
    </PageShell>
  )
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
