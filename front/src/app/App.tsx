import { QueryClient, QueryClientProvider, useMutation, useQuery } from '@tanstack/react-query'
import { Button, Card, Chip, Input, Spinner } from '@heroui/react'
import styled from '@emotion/styled'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import type { SyntheticEvent } from 'react'
import { api } from '../shared/api/client'
import type { AnswerResult, Difficulty, QuizQuestion } from '../entities/quiz/types'
import type { TeamMember, UserTeam } from '../entities/team/types'

const queryClient = new QueryClient()

const Screen = styled.main`
  min-height: 100vh;
  background:
    radial-gradient(circle at 20% -10%, rgba(87, 139, 255, 0.24), transparent 34rem),
    linear-gradient(180deg, #f7f9ff 0%, #eef3ff 48%, #f8fafc 100%);
  color: #101828;
  font-family:
    'Noto Sans KR', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
`

const AppFrame = styled.div`
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 28px 0 56px;
`

const TopBar = styled.nav`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
`

const Brand = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 900;
`

const BrandIcon = styled.div`
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, #2f6df6, #7c4dff);
  color: white;
  box-shadow: 0 14px 30px rgba(47, 109, 246, 0.26);
`

const Hero = styled.section`
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: end;
  margin-bottom: 22px;

  @media (max-width: 780px) {
    grid-template-columns: 1fr;
  }
`

const HeroCopy = styled.div`
  display: grid;
  gap: 10px;
`

const Eyebrow = styled.span`
  color: #3867d6;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
`

const Title = styled.h1`
  max-width: 720px;
  margin: 0;
  font-size: clamp(34px, 6vw, 64px);
  line-height: 0.98;
  letter-spacing: -0.06em;
`

const Description = styled.p`
  max-width: 680px;
  margin: 0;
  color: #667085;
  font-size: 16px;
  line-height: 1.7;
`

const MainGrid = styled.div`
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
  gap: 20px;

  @media (max-width: 960px) {
    grid-template-columns: 1fr;
  }
`

const CardSurface = styled.div`
  .heroui-card {
    border: 1px solid rgba(44, 62, 80, 0.08);
    border-radius: 28px;
    box-shadow: 0 24px 70px rgba(30, 41, 59, 0.12);
  }
`

const SectionHeader = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
`

const SectionTitle = styled.h2`
  margin: 0;
  font-size: 22px;
  letter-spacing: -0.03em;
`

const SectionSubtitle = styled.p`
  margin: 6px 0 0;
  color: #667085;
  line-height: 1.5;
`

const EntryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
`

const EntryCard = styled.article`
  display: grid;
  grid-template-columns: 70px minmax(0, 1fr);
  gap: 12px;
  min-height: 150px;
  padding: 14px;
  border: 1px solid #e8edf7;
  border-radius: 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
`

const PokemonArtwork = styled.img`
  width: 70px;
  height: 70px;
  align-self: center;
  object-fit: contain;
  filter: drop-shadow(0 12px 16px rgba(15, 23, 42, 0.16));
`

const EmptyArtwork = styled.div`
  display: grid;
  width: 70px;
  height: 70px;
  align-self: center;
  place-items: center;
  border-radius: 24px;
  background: #eef4ff;
  color: #98a2b3;
  font-size: 28px;
  font-weight: 900;
`

const EntryFields = styled.div`
  display: grid;
  gap: 8px;
  min-width: 0;

  .input {
    width: 100%;
    min-width: 0;
  }
`

const CompactFieldRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 0.7fr;
  gap: 8px;
`

const MiniMeta = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
`

const DifficultyList = styled.div`
  display: grid;
  gap: 12px;
`

const DifficultyButton = styled.button<{ selected?: boolean }>`
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
  width: 100%;
  padding: 16px;
  border: 1px solid ${({ selected }) => (selected ? '#2f6df6' : '#e8edf7')};
  border-radius: 22px;
  background: ${({ selected }) => (selected ? 'linear-gradient(135deg, #eff5ff, #ffffff)' : '#ffffff')};
  color: inherit;
  cursor: pointer;
  text-align: left;
  box-shadow: ${({ selected }) => (selected ? '0 14px 34px rgba(47, 109, 246, 0.14)' : 'none')};
`

const DifficultyIcon = styled.div`
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 16px;
  background: #eef4ff;
  color: #2f6df6;
  font-weight: 900;
`

const QuizPanel = styled.div`
  display: grid;
  min-height: 420px;
  place-items: center;
  padding: 14px 0;
`

const QuizCard = styled(motion.div)`
  width: min(430px, 100%);
  min-height: 430px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 16px;
  padding: 22px;
  border: 1px solid #dce7ff;
  border-radius: 34px;
  background: linear-gradient(180deg, #ffffff 0%, #f2f7ff 100%);
  box-shadow: 0 26px 90px rgba(47, 109, 246, 0.18);
  touch-action: pan-y;
`

const VersusArea = styled.div`
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 10px;
  align-items: center;
`

const PokemonSide = styled.div`
  display: grid;
  justify-items: center;
  gap: 8px;
  min-width: 0;
`

const QuizArtwork = styled.img`
  width: 122px;
  height: 122px;
  object-fit: contain;
  filter: drop-shadow(0 18px 18px rgba(15, 23, 42, 0.18));
`

const VersusBadge = styled.div`
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  border-radius: 50%;
  background: #101828;
  color: white;
  font-weight: 900;
  letter-spacing: -0.08em;
`

const Statement = styled.h3`
  margin: 0;
  text-align: center;
  font-size: clamp(24px, 5vw, 34px);
  line-height: 1.15;
  letter-spacing: -0.04em;
`

const SpeedMystery = styled.div`
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  color: #667085;
  font-weight: 800;
`

const ActionRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
`

const ResultBox = styled.div<{ correct: boolean }>`
  margin-top: 12px;
  padding: 14px;
  border-radius: 18px;
  background: ${({ correct }) => (correct ? '#ecfdf3' : '#fff1f3')};
  color: ${({ correct }) => (correct ? '#027a48' : '#b42318')};
  font-weight: 800;
  line-height: 1.5;
`

const FooterNote = styled.p`
  margin: 14px 0 0;
  color: #98a2b3;
  font-size: 13px;
  line-height: 1.5;
`

const defaultMember = (slot: number): TeamMember => ({
  slot,
  pokemonId: slot === 1 ? 'garchomp' : `pokemon-${slot}`,
  pokemonName: slot === 1 ? 'Garchomp' : '',
  nationalDexNumber: slot === 1 ? 445 : null,
  imageAssets: slot === 1 ? imageAssetsFromDex(445) : null,
  baseStatsSnapshot: { hp: 1, atk: 1, def: 1, spa: 1, spd: 1, spe: 80 },
  level: 50,
  nature: 'Jolly',
  ability: null,
  item: null,
  evs: { spe: 252 },
  ivs: { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 },
})

function imageAssetsFromDex(nationalDexNumber: number) {
  const padded = String(nationalDexNumber).padStart(3, '0')
  return {
    primaryArtworkUrl: `https://assets.pokemon.com/assets/cms2/img/pokedex/full/${padded}.png`,
    fallbackArtworkUrl: `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${nationalDexNumber}.png`,
    spriteUrl: `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${nationalDexNumber}.png`,
    sourceName: 'pokemon-official+pokedex-pokeapi',
    hotlinkPolicy: 'unknown',
  }
}

function artworkUrl(member: TeamMember): string | null {
  return member.imageAssets?.primaryArtworkUrl ?? member.imageAssets?.fallbackArtworkUrl ?? null
}

function handleImageError(event: SyntheticEvent<HTMLImageElement>, member: TeamMember) {
  const fallback = member.imageAssets?.fallbackArtworkUrl
  if (fallback && event.currentTarget.src !== fallback) {
    event.currentTarget.src = fallback
    return
  }
  event.currentTarget.style.display = 'none'
}

function AppContent() {
  const [teamDraft, setTeamDraft] = useState<UserTeam>({
    teamName: 'main',
    format: 'pokemon_champions',
    members: Array.from({ length: 6 }, (_, index) => defaultMember(index + 1)),
  })
  const [selectedDifficulty, setSelectedDifficulty] = useState<Difficulty | null>(null)
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [questionIndex, setQuestionIndex] = useState(0)
  const [lastResult, setLastResult] = useState<AnswerResult | null>(null)

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
  const answerQuestion = useMutation({
    mutationFn: ({ id, answer }: { id: string; answer: boolean }) => api.answerQuestion(id, answer),
  })

  useEffect(() => {
    if (teamQuery.data) {
      const filledMembers = Array.from({ length: 6 }, (_, index) => teamQuery.data.members[index] ?? defaultMember(index + 1))
      setTeamDraft({ ...teamQuery.data, members: filledMembers })
    }
  }, [teamQuery.data])

  const currentQuestion = questions[questionIndex]
  const completedCount = Math.min(questionIndex, questions.length)

  function updateMember(slot: number, patch: Partial<TeamMember>) {
    setTeamDraft((team) => ({
      ...team,
      members: team.members.map((member) => (member.slot === slot ? { ...member, ...patch } : member)),
    }))
  }

  function updateName(slot: number, pokemonName: string) {
    updateMember(slot, {
      pokemonName,
      pokemonId: pokemonName.toLowerCase().replace(/\s+/g, '-'),
    })
  }

  function updateBaseSpeed(slot: number, spe: number) {
    const member = teamDraft.members.find((candidate) => candidate.slot === slot)
    if (!member) return
    updateMember(slot, { baseStatsSnapshot: { ...member.baseStatsSnapshot, spe } })
  }

  function updateNationalDexNumber(slot: number, nationalDexNumber: number) {
    updateMember(slot, {
      nationalDexNumber,
      imageAssets: nationalDexNumber > 0 ? imageAssetsFromDex(nationalDexNumber) : null,
    })
  }

  async function answer(answerValue: boolean) {
    if (!currentQuestion) return
    const result = await answerQuestion.mutateAsync({ id: currentQuestion.id, answer: answerValue })
    setLastResult(result)
    setQuestionIndex((index) => index + 1)
  }

  function startQuiz(difficulty: Difficulty) {
    setSelectedDifficulty(difficulty)
    generateQuiz.mutate(difficulty)
  }

  return (
    <Screen>
      <AppFrame>
        <TopBar>
          <Brand>
            <BrandIcon>⚡</BrandIcon>
            <span>Champions Speed Lab</span>
          </Brand>
          <Chip color="accent" variant="soft">Hero UI v3 preview</Chip>
        </TopBar>

        <Hero>
          <HeroCopy>
            <Eyebrow>Speed comparison trainer</Eyebrow>
            <Title>내 엔트리와 메타 샘플의 스피드 티어를 빠르게 맞혀요.</Title>
            <Description>
              공식/PokeAPI 이미지 URL을 species 데이터에 저장하고, 퀴즈 카드는 정답 제출 전까지 속도를 숨깁니다.
              지금 메타 데이터는 개발 fixture이며 실제 Champions 크롤러 데이터와 분리됩니다.
            </Description>
          </HeroCopy>
          <Button size="lg" variant="primary" onPress={() => startQuiz(selectedDifficulty ?? 'easy')} isDisabled={generateQuiz.isPending}>
            쉬움으로 바로 시작
          </Button>
        </Hero>

        <MainGrid>
          <CardSurface>
            <Card className="heroui-card">
              <Card.Header>
                <SectionHeader>
                  <div>
                    <SectionTitle>내 엔트리</SectionTitle>
                    <SectionSubtitle>6개 슬롯에 이름, National Dex, base Speed, 노력치 정보를 입력합니다.</SectionSubtitle>
                  </div>
                  <Chip variant="soft">{teamDraft.members.filter((member) => member.pokemonName).length}/6</Chip>
                </SectionHeader>
              </Card.Header>
              <Card.Content>
                <EntryGrid>
                  {teamDraft.members.map((member) => (
                    <EntryCard key={member.slot}>
                      {artworkUrl(member) ? (
                        <PokemonArtwork src={artworkUrl(member) ?? undefined} alt={member.pokemonName || `slot ${member.slot}`} onError={(event) => handleImageError(event, member)} />
                      ) : (
                        <EmptyArtwork>?</EmptyArtwork>
                      )}
                      <EntryFields>
                        <MiniMeta>
                          <Chip size="sm" color="accent" variant="soft">Slot {member.slot}</Chip>
                          <Chip size="sm" variant="soft">Spe {member.baseStatsSnapshot.spe}</Chip>
                        </MiniMeta>
                        <Input fullWidth aria-label={`slot ${member.slot} pokemon name`} value={member.pokemonName} placeholder="Pokémon name" onChange={(event) => updateName(member.slot, event.target.value)} />
                        <CompactFieldRow>
                          <Input fullWidth aria-label={`slot ${member.slot} national dex`} type="number" value={String(member.nationalDexNumber ?? '')} placeholder="Dex" onChange={(event) => updateNationalDexNumber(member.slot, Number(event.target.value))} />
                          <Input fullWidth aria-label={`slot ${member.slot} base speed`} type="number" value={String(member.baseStatsSnapshot.spe)} placeholder="Base Spe" onChange={(event) => updateBaseSpeed(member.slot, Number(event.target.value))} />
                        </CompactFieldRow>
                        <CompactFieldRow>
                          <Input fullWidth aria-label={`slot ${member.slot} nature`} value={member.nature} placeholder="Nature" onChange={(event) => updateMember(member.slot, { nature: event.target.value })} />
                          <Input fullWidth aria-label={`slot ${member.slot} speed ev`} type="number" value={String(member.evs.spe ?? 0)} placeholder="EV" onChange={(event) => updateMember(member.slot, { evs: { ...member.evs, spe: Number(event.target.value) } })} />
                        </CompactFieldRow>
                      </EntryFields>
                    </EntryCard>
                  ))}
                </EntryGrid>
                <ActionRow style={{ marginTop: 18 }}>
                  <Button variant="primary" onPress={() => saveTeam.mutate(teamDraft)} isDisabled={saveTeam.isPending}>
                    {saveTeam.isPending ? '저장 중...' : '엔트리 저장'}
                  </Button>
                  <Button variant="outline" onPress={() => startQuiz(selectedDifficulty ?? 'easy')} isDisabled={generateQuiz.isPending}>
                    퀴즈 생성
                  </Button>
                </ActionRow>
              </Card.Content>
            </Card>
          </CardSurface>

          <CardSurface>
            <Card className="heroui-card">
              <Card.Header>
                <SectionHeader>
                  <div>
                    <SectionTitle>퀴즈</SectionTitle>
                    <SectionSubtitle>난이도를 고르면 서버에서 yes/no 문제를 생성합니다.</SectionSubtitle>
                  </div>
                  <Chip color="accent" variant="soft">{completedCount}/{questions.length || 5}</Chip>
                </SectionHeader>
              </Card.Header>
              <Card.Content>
                <DifficultyList>
                  {difficultiesQuery.data?.map((difficulty, index) => (
                    <DifficultyButton key={difficulty.id} selected={selectedDifficulty === difficulty.id} onClick={() => startQuiz(difficulty.id)}>
                      <DifficultyIcon>{index + 1}</DifficultyIcon>
                      <div>
                        <strong>{difficulty.label}</strong>
                        <SectionSubtitle>{difficulty.description}</SectionSubtitle>
                      </div>
                      <Chip size="sm" color={selectedDifficulty === difficulty.id ? 'accent' : 'default'} variant="soft">
                        {selectedDifficulty === difficulty.id ? 'selected' : 'start'}
                      </Chip>
                    </DifficultyButton>
                  ))}
                </DifficultyList>

                <QuizPanel>
                  {generateQuiz.isPending && (
                    <div style={{ display: 'grid', justifyItems: 'center', gap: 12 }}>
                      <Spinner color="accent" size="lg" />
                      <Description>문제 생성 중... 내 엔트리와 메타 샘플의 base Speed를 비교하고 있어요.</Description>
                    </div>
                  )}

                  {!generateQuiz.isPending && currentQuestion && (
                    <AnimatePresence mode="wait">
                      <QuizCard
                        key={currentQuestion.id}
                        drag="x"
                        dragConstraints={{ left: 0, right: 0 }}
                        onDragEnd={(_, info) => {
                          if (info.offset.x > 90) void answer(true)
                          if (info.offset.x < -90) void answer(false)
                        }}
                        initial={{ opacity: 0, y: 18 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.96 }}
                      >
                        <MiniMeta>
                          <Chip color="accent" variant="soft">{currentQuestion.difficulty}</Chip>
                          <Chip variant="soft">← No / Yes →</Chip>
                        </MiniMeta>
                        <div>
                          <VersusArea>
                            <PokemonSide>
                              <QuizArtwork src={artworkUrl(currentQuestion.subject.build) ?? undefined} alt={currentQuestion.subject.build.pokemonName} onError={(event) => handleImageError(event, currentQuestion.subject.build)} />
                              <strong>{currentQuestion.subject.build.pokemonName}</strong>
                            </PokemonSide>
                            <VersusBadge>VS</VersusBadge>
                            <PokemonSide>
                              <QuizArtwork src={artworkUrl(currentQuestion.opponent.build) ?? undefined} alt={currentQuestion.opponent.build.pokemonName} onError={(event) => handleImageError(event, currentQuestion.opponent.build)} />
                              <strong>{currentQuestion.opponent.build.pokemonName}</strong>
                            </PokemonSide>
                          </VersusArea>
                          <SpeedMystery>
                            <span>Speed ?</span>
                            <span>·</span>
                            <span>Speed ?</span>
                          </SpeedMystery>
                        </div>
                        <Statement>{currentQuestion.statement}</Statement>
                        <ActionRow>
                          <Button variant="primary" onPress={() => void answer(false)}>← 틀림</Button>
                          <Button variant="primary" onPress={() => void answer(true)}>맞음 →</Button>
                        </ActionRow>
                      </QuizCard>
                    </AnimatePresence>
                  )}

                  {!generateQuiz.isPending && questions.length > 0 && !currentQuestion && (
                    <Description>이번 세트 완료! 다른 난이도로 다시 시작해보세요.</Description>
                  )}
                </QuizPanel>

                {lastResult && (
                  <ResultBox correct={lastResult.correct}>
                    {lastResult.correct ? '정답!' : '오답!'} {lastResult.explanation}
                    <br />
                    공개 Speed: {lastResult.subjectSpeed} vs {lastResult.opponentSpeed}
                  </ResultBox>
                )}
                <FooterNote>이미지는 DB의 공식/PokeAPI URL을 우선 사용하고, 실패 시 fallback URL로 교체합니다.</FooterNote>
              </Card.Content>
            </Card>
          </CardSurface>
        </MainGrid>
      </AppFrame>
    </Screen>
  )
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
