import { QueryClient, QueryClientProvider, useMutation, useQuery } from '@tanstack/react-query'
import { Button, Chip, Spinner } from '@heroui/react'
import styled from '@emotion/styled'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import type { SyntheticEvent } from 'react'
import { api } from '../shared/api/client'
import type { AnswerResult, Difficulty, DifficultyOption, QuizQuestion } from '../entities/quiz/types'
import type { TeamMember, UserTeam } from '../entities/team/types'

const queryClient = new QueryClient()

type ScreenName = 'entry' | 'difficulty' | 'quiz' | 'create'

const Screen = styled.main`
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 18px;
  background: #e9e9ec;
  color: #111827;
  font-family:
    'Noto Sans KR', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
`

const Phone = styled.div`
  position: relative;
  width: min(100%, 390px);
  height: min(844px, calc(100vh - 36px));
  min-height: 720px;
  overflow: hidden;
  border-radius: 34px;
  background: #f8f8f9;
  box-shadow:
    0 28px 90px rgba(15, 23, 42, 0.16),
    inset 0 0 0 8px rgba(255, 255, 255, 0.72);

  @media (max-width: 430px) {
    width: 100%;
    height: calc(100vh - 16px);
    min-height: 680px;
    border-radius: 28px;
  }
`

const PhoneContent = styled.div`
  position: relative;
  height: 100%;
  padding: 20px 20px 18px;
  overflow: hidden;
`

const StatusBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 22px;
  margin-bottom: 12px;
  color: #111827;
  font-size: 12px;
  font-weight: 900;
`

const Signal = styled.div`
  display: flex;
  gap: 3px;

  span {
    width: 5px;
    height: 10px;
    border-radius: 1px;
    background: #4b5563;
  }
`

const Header = styled.header`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
`

const HeaderCopy = styled.div`
  min-width: 0;
  flex: 1;
`

const PageTitle = styled.h1`
  margin: 0;
  font-size: 21px;
  line-height: 1.15;
  letter-spacing: -0.05em;
`

const PageSubtitle = styled.p`
  margin: 3px 0 0;
  color: #7b8089;
  font-size: 12px;
  font-weight: 700;
`

const IconButton = styled.button`
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  place-items: center;
  border: 0;
  border-radius: 11px;
  background: #ffffff;
  color: #111827;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
  cursor: pointer;
`

const FilterRow = styled.div`
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 12px;
  overflow-x: auto;
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
`

const TinyLabel = styled.span`
  flex: 0 0 auto;
  color: #69707b;
  font-size: 11px;
  font-weight: 800;
`

const Pill = styled.button<{ active?: boolean }>`
  flex: 0 0 auto;
  min-width: 44px;
  height: 27px;
  padding: 0 13px;
  border: 0;
  border-radius: 999px;
  background: ${({ active }) => (active ? '#0b7bf3' : '#ffffff')};
  color: ${({ active }) => (active ? '#ffffff' : '#111827')};
  font-size: 12px;
  font-weight: 900;
  box-shadow: ${({ active }) => (active ? '0 8px 18px rgba(11, 123, 243, 0.24)' : '0 4px 12px rgba(15, 23, 42, 0.05)')};
`

const EntryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 11px;
  max-height: calc(100% - 164px);
  overflow-y: auto;
  padding: 1px 1px 12px;
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
`

const EntryCard = styled.button`
  width: 100%;
  min-height: 148px;
  border: 0;
  color: inherit;
  text-align: inherit;
  cursor: pointer;
  padding: 9px 9px 8px;
  border-radius: 17px;
  background: #ffffff;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.055);
`

const ArtPanel = styled.div`
  position: relative;
  display: grid;
  height: 72px;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(180deg, #fbfbfc 0%, #f5f6f8 100%);
`

const LevelBadge = styled.span`
  position: absolute;
  top: 5px;
  right: 6px;
  color: #111827;
  font-size: 9px;
  font-weight: 900;
`

const PokemonArtwork = styled.img`
  max-width: 78px;
  max-height: 68px;
  object-fit: contain;
  filter: drop-shadow(0 8px 10px rgba(15, 23, 42, 0.16));
`

const EmptySlot = styled.div`
  display: grid;
  height: 72px;
  place-items: center;
  border-radius: 14px;
  background: #fbfbfc;
  color: #a0a7b2;
`

const PlusButton = styled.div`
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 13px;
  background: #f1f3f6;
  font-size: 22px;
  font-weight: 500;
`

const EntryName = styled.h2`
  margin: 8px 0 5px;
  text-align: center;
  font-size: 13px;
  line-height: 1.2;
  letter-spacing: -0.04em;
`

const TypeRow = styled.div`
  display: flex;
  justify-content: center;
  gap: 5px;
  min-height: 14px;
`

const TypeDot = styled.span<{ color: string }>`
  width: 12px;
  height: 12px;
  border-radius: 4px;
  background: ${({ color }) => color};
`

const StatLine = styled.div`
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 9px;
  padding-top: 8px;
  border-top: 1px solid #edf0f4;
  color: #9aa1ab;
  font-size: 11px;
  font-weight: 800;

  strong {
    color: #0074f5;
    font-size: 16px;
    line-height: 1;
  }
`

const BottomAction = styled.div`
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 18px;

  button {
    width: 100%;
    height: 50px;
    border-radius: 15px;
    font-weight: 900;
    box-shadow: 0 12px 26px rgba(0, 116, 245, 0.25);
  }
`

const DifficultyList = styled.div`
  display: grid;
  gap: 10px;
  margin-top: 12px;
`

const DifficultyCard = styled.button<{ selected?: boolean; tone: string }>`
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 14px;
  gap: 12px;
  align-items: center;
  min-height: 76px;
  width: 100%;
  padding: 13px 13px 13px 10px;
  border: 1.5px solid ${({ selected }) => (selected ? '#2b8cff' : '#e6e8ed')};
  border-radius: 16px;
  background: #ffffff;
  text-align: left;
  box-shadow: ${({ selected }) => (selected ? '0 12px 22px rgba(43, 140, 255, 0.12)' : '0 6px 16px rgba(15, 23, 42, 0.045)')};
  cursor: pointer;

  .number {
    display: grid;
    width: 34px;
    height: 34px;
    place-items: center;
    border-radius: 11px;
    background: ${({ tone }) => tone};
    color: #111827;
    font-weight: 900;
  }

  .arrow {
    color: #b9bec7;
    font-weight: 900;
  }
`

const DifficultyName = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: -0.04em;
`

const DifficultyDesc = styled.p`
  margin: 3px 0 6px;
  color: #7d8490;
  font-size: 11px;
  font-weight: 700;
`

const TagRow = styled.div`
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
`

const MiniTag = styled.span`
  padding: 4px 7px;
  border-radius: 999px;
  background: #f1f2f4;
  color: #626a75;
  font-size: 10px;
  font-weight: 900;
`

const QuizTop = styled.div`
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: center;
  margin-bottom: 22px;
`

const QuizPrompt = styled.div`
  text-align: center;
  margin-bottom: 36px;
`

const QuizTitle = styled.h1`
  margin: 8px 0 5px;
  font-size: 20px;
  line-height: 1.18;
  letter-spacing: -0.06em;
`

const QuizHint = styled.p`
  margin: 0;
  color: #8b929d;
  font-size: 12px;
  font-weight: 700;
`

const QuizCard = styled(motion.div)`
  min-height: 300px;
  padding: 20px 15px 14px;
  border-radius: 24px;
  background: #ffffff;
  box-shadow: 0 20px 52px rgba(15, 23, 42, 0.10);
  touch-action: pan-y;
`

const VersusArea = styled.div`
  display: grid;
  grid-template-columns: 1fr 38px 1fr;
  gap: 6px;
  align-items: start;
`

const QuizSide = styled.div`
  display: grid;
  justify-items: center;
  gap: 7px;
`

const SideLabel = styled.span<{ color: string }>`
  color: ${({ color }) => color};
  font-size: 9px;
  font-weight: 1000;
  letter-spacing: 0.06em;
`

const QuizArtCircle = styled.div`
  display: grid;
  width: 92px;
  height: 92px;
  place-items: center;
  border-radius: 50%;
  background: #f7f8fa;
`

const QuizArtwork = styled.img`
  max-width: 96px;
  max-height: 86px;
  object-fit: contain;
  filter: drop-shadow(0 10px 12px rgba(15, 23, 42, 0.16));
`

const VersusBadge = styled.div`
  display: grid;
  width: 34px;
  height: 34px;
  margin-top: 48px;
  place-items: center;
  border-radius: 50%;
  background: #111827;
  color: white;
  font-size: 12px;
  font-weight: 1000;
`

const PokemonName = styled.strong`
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  letter-spacing: -0.04em;
`

const Mystery = styled.div`
  display: grid;
  gap: 4px;
  justify-items: center;
  margin-top: 5px;
  color: #a0a7b2;
  font-size: 10px;
  font-weight: 800;

  .circle {
    display: grid;
    width: 32px;
    height: 32px;
    place-items: center;
    border-radius: 50%;
    background: #f0f1f3;
    color: #9aa1ab;
    font-size: 16px;
    font-weight: 1000;
  }
`

const AppliedRules = styled.div`
  margin-top: 72px;
  padding-top: 12px;
  border-top: 1px solid #edf0f4;
`

const RuleLabel = styled.div`
  margin-bottom: 7px;
  color: #8a929d;
  font-size: 11px;
  font-weight: 800;
`

const SwipeActions = styled.div`
  position: absolute;
  left: 48px;
  right: 48px;
  bottom: 34px;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 1000;

  button {
    border: 0;
    background: transparent;
    font: inherit;
    cursor: pointer;
  }

  .no {
    color: #ff3d75;
  }

  .yes {
    color: #22c55e;
  }
`

const ResultToast = styled.div<{ correct: boolean }>`
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 78px;
  padding: 12px;
  border-radius: 16px;
  background: ${({ correct }) => (correct ? '#ecfdf3' : '#fff1f3')};
  color: ${({ correct }) => (correct ? '#027a48' : '#b42318')};
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);
  font-size: 12px;
  font-weight: 800;
  line-height: 1.45;
`

const LoadingLayer = styled.div`
  display: grid;
  min-height: 420px;
  place-items: center;
  color: #7b8089;
  font-size: 13px;
  font-weight: 800;
`

const CreateScroll = styled.div`
  height: calc(100% - 112px);
  overflow-y: auto;
  padding: 2px 2px 82px;
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
`

const FormHero = styled.div`
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr) 56px;
  gap: 9px;
  align-items: end;
  margin-bottom: 6px;
`

const PreviewTile = styled.div`
  display: grid;
  height: 68px;
  place-items: center;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
`

const FieldGroup = styled.div`
  display: grid;
  gap: 5px;
`

const FieldLabel = styled.label`
  display: grid;
  gap: 5px;
  color: #222834;
  font-size: 10px;
  font-weight: 900;
`

const TextField = styled.input`
  width: 100%;
  height: 34px;
  min-width: 0;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  padding: 0 11px;
  color: #111827;
  font-size: 12px;
  font-weight: 800;
  outline: none;

  &:focus {
    border-color: #0b7bf3;
    box-shadow: 0 0 0 3px rgba(11, 123, 243, 0.10);
  }
`

const SelectLike = styled.button`
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 34px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  padding: 0 11px;
  color: #7b8089;
  font-size: 11px;
  font-weight: 800;
`

const TwoColumnFields = styled.div`
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 8px;
`

const FullField = styled.div`
  margin-bottom: 8px;
`

const TypeChipRow = styled.div`
  display: flex;
  gap: 6px;
  margin: 3px 0 10px 78px;
`

const SmallTypeChip = styled.span<{ color: string }>`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 18px;
  padding: 0 7px;
  border-radius: 999px;
  background: #f2f4f7;
  color: #5f6875;
  font-size: 9px;
  font-weight: 900;

  &::before {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: ${({ color }) => color};
  }
`

const StatHeader = styled.div`
  display: grid;
  grid-template-columns: 38px 34px minmax(0, 1fr) 30px 34px;
  gap: 7px;
  align-items: center;
  margin: 12px 0 7px;
  color: #6b7280;
  font-size: 9px;
  font-weight: 1000;
`

const StatRow = styled.div`
  display: grid;
  grid-template-columns: 38px 34px minmax(0, 1fr) 30px 34px;
  gap: 7px;
  align-items: center;
  min-height: 31px;
  color: #111827;
  font-size: 10px;
  font-weight: 900;
`

const StatValue = styled.span`
  color: #5d6673;
  text-align: center;
  font-size: 10px;
  font-weight: 900;
`

const RangeWrap = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;

  input {
    width: 100%;
    accent-color: #f97316;
  }
`

const TinyRoundButton = styled.button`
  display: grid;
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: #eef0f3;
  color: #8d95a1;
  font-size: 11px;
  font-weight: 900;
`

const typeColors = ['#79d19d', '#a78bfa', '#f59e0b', '#ef4444', '#60a5fa', '#f472b6']
const difficultyTones = ['#c8ffe3', '#dbeafe', '#ffe4a8', '#ffd1e1', '#ede9fe']

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

function difficultyTitle(option: DifficultyOption): string {
  const byId: Record<Difficulty, string> = {
    easy: '쉬움',
    normal: '보통',
    hard: '어려움',
    expert: '전문가',
    master: '마스터',
  }
  return byId[option.id] ?? option.label
}

function difficultyTags(id: Difficulty): string[] {
  const tags: Record<Difficulty, string[]> = {
    easy: ['베이스 속도'],
    normal: ['베이스 속도', '실전 스탯', '성격'],
    hard: ['+ 날씨', '특성', '노력치/성격'],
    expert: ['+ 날씨', '특성', '노력치/성격'],
    master: ['+ 상태이상', '전체 변수'],
  }
  return tags[id]
}

function KoreanName({ member }: { member: TeamMember }) {
  return <>{member.pokemonName || '포켓몬 추가'}</>
}

function EntryScreen({ teamDraft, onStart, onOpenCreate }: { teamDraft: UserTeam; onStart: () => void; onOpenCreate: (slot: number) => void }) {
  return (
    <>
      <Header>
        <HeaderCopy>
          <PageTitle>내 엔트리</PageTitle>
          <PageSubtitle>최대 6마리</PageSubtitle>
        </HeaderCopy>
      </Header>

      <FilterRow>
        <TinyLabel>표시</TinyLabel>
        {['스피드', 'HP', '공격', '방어', '특공', '특방'].map((label, index) => (
          <Pill key={label} active={index === 0}>{label}</Pill>
        ))}
      </FilterRow>

      <EntryGrid>
        {teamDraft.members.map((member, index) => {
          const hasPokemon = Boolean(member.pokemonName)
          return (
            <EntryCard key={member.slot} type="button" onClick={() => onOpenCreate(member.slot)}>
              {hasPokemon ? (
                <>
                  <ArtPanel>
                    <LevelBadge>Lv {member.level}</LevelBadge>
                    {artworkUrl(member) ? (
                      <PokemonArtwork src={artworkUrl(member) ?? undefined} alt={member.pokemonName} onError={(event) => handleImageError(event, member)} />
                    ) : (
                      <PlusButton>?</PlusButton>
                    )}
                  </ArtPanel>
                  <EntryName><KoreanName member={member} /></EntryName>
                  <TypeRow>
                    <TypeDot color={typeColors[index % typeColors.length]} />
                    <TypeDot color={typeColors[(index + 1) % typeColors.length]} />
                  </TypeRow>
                  <StatLine>
                    <span>스피드</span>
                    <strong>{member.baseStatsSnapshot.spe}</strong>
                  </StatLine>
                </>
              ) : (
                <>
                  <EmptySlot><PlusButton>+</PlusButton></EmptySlot>
                  <EntryName>포켓몬 추가</EntryName>
                  <TypeRow />
                  <StatLine>
                    <span>스피드</span>
                    <strong>-</strong>
                  </StatLine>
                </>
              )}
            </EntryCard>
          )
        })}
      </EntryGrid>

      <BottomAction>
        <Button variant="primary" onPress={onStart}>퀴즈 시작하기</Button>
      </BottomAction>
    </>
  )
}

function DifficultyScreen({
  options,
  selectedDifficulty,
  onBack,
  onSelect,
  onStart,
}: {
  options: DifficultyOption[] | undefined
  selectedDifficulty: Difficulty | null
  onBack: () => void
  onSelect: (difficulty: Difficulty) => void
  onStart: () => void
}) {
  const selectedLabel = selectedDifficulty ? difficultyTitle({ id: selectedDifficulty, label: selectedDifficulty, description: '' }) : '난이도'
  return (
    <>
      <Header>
        <IconButton onClick={onBack}>‹</IconButton>
        <HeaderCopy>
          <PageTitle>난이도 선택</PageTitle>
          <PageSubtitle>스피드 비교 · 6마리 엔트리</PageSubtitle>
        </HeaderCopy>
      </Header>

      <DifficultyList>
        {options?.map((option, index) => {
          const selected = selectedDifficulty === option.id
          return (
            <DifficultyCard key={option.id} selected={selected} tone={difficultyTones[index % difficultyTones.length]} onClick={() => onSelect(option.id)}>
              <span className="number">{index + 1}</span>
              <div>
                <DifficultyName>
                  {difficultyTitle(option)}
                  {selected && <Chip size="sm" color="accent" variant="soft">선택됨</Chip>}
                </DifficultyName>
                <DifficultyDesc>{option.description}</DifficultyDesc>
                <TagRow>
                  {difficultyTags(option.id).map((tag) => <MiniTag key={tag}>{tag}</MiniTag>)}
                </TagRow>
              </div>
              <span className="arrow">›</span>
            </DifficultyCard>
          )
        })}
      </DifficultyList>

      <BottomAction>
        <Button variant="primary" onPress={onStart}>{selectedLabel}으로 시작</Button>
      </BottomAction>
    </>
  )
}

function QuizScreen({
  difficulty,
  currentQuestion,
  questionIndex,
  total,
  lastResult,
  isLoading,
  onAnswer,
}: {
  difficulty: Difficulty | null
  currentQuestion: QuizQuestion | undefined
  questionIndex: number
  total: number
  lastResult: AnswerResult | null
  isLoading: boolean
  onAnswer: (answer: boolean) => void
}) {
  return (
    <>
      <QuizTop>
        <Chip color="success" size="sm" variant="soft">{difficulty ? difficultyTitle({ id: difficulty, label: difficulty, description: '' }) : '쉬움'}</Chip>
        <PageSubtitle>{Math.min(questionIndex + 1, total || 1)} / {total || 5}</PageSubtitle>
      </QuizTop>

      <QuizPrompt>
        <QuizTitle>내 포켓몬이 무쇠손보다 빠를까?</QuizTitle>
        <QuizHint>속도 수치는 숨기기 있어요 · 왼/오른 판단</QuizHint>
      </QuizPrompt>

      {isLoading && (
        <LoadingLayer>
          <div style={{ display: 'grid', justifyItems: 'center', gap: 12 }}>
            <Spinner color="accent" />
            <span>문제 생성 중...</span>
          </div>
        </LoadingLayer>
      )}

      {!isLoading && currentQuestion && (
        <AnimatePresence mode="wait">
          <QuizCard
            key={currentQuestion.id}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            onDragEnd={(_, info) => {
              if (info.offset.x > 90) onAnswer(true)
              if (info.offset.x < -90) onAnswer(false)
            }}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96 }}
          >
            <VersusArea>
              <QuizSide>
                <SideLabel color="#0b7bf3">MY</SideLabel>
                <QuizArtCircle>
                  <QuizArtwork src={artworkUrl(currentQuestion.subject.build) ?? undefined} alt={currentQuestion.subject.build.pokemonName} onError={(event) => handleImageError(event, currentQuestion.subject.build)} />
                </QuizArtCircle>
                <PokemonName>{currentQuestion.subject.build.pokemonName}</PokemonName>
                <TypeRow><TypeDot color="#db7da2" /><TypeDot color="#a78bfa" /></TypeRow>
                <Mystery><span className="circle">?</span><span>속도</span></Mystery>
              </QuizSide>
              <VersusBadge>VS</VersusBadge>
              <QuizSide>
                <SideLabel color="#ff3d75">META</SideLabel>
                <QuizArtCircle>
                  <QuizArtwork src={artworkUrl(currentQuestion.opponent.build) ?? undefined} alt={currentQuestion.opponent.build.pokemonName} onError={(event) => handleImageError(event, currentQuestion.opponent.build)} />
                </QuizArtCircle>
                <PokemonName>{currentQuestion.opponent.build.pokemonName}</PokemonName>
                <TypeRow><TypeDot color="#dc2626" /><TypeDot color="#facc15" /></TypeRow>
                <Mystery><span className="circle">?</span><span>속도</span></Mystery>
              </QuizSide>
            </VersusArea>

            <AppliedRules>
              <RuleLabel>적용 변수</RuleLabel>
              <TagRow><MiniTag>● 베이스 속도 비교</MiniTag></TagRow>
            </AppliedRules>
          </QuizCard>
        </AnimatePresence>
      )}

      {!isLoading && total > 0 && !currentQuestion && <LoadingLayer>이번 세트 완료!</LoadingLayer>}

      {lastResult && (
        <ResultToast correct={lastResult.correct}>
          {lastResult.correct ? '정답!' : '오답!'} {lastResult.explanation}<br />
          Speed: {lastResult.subjectSpeed} vs {lastResult.opponentSpeed}
        </ResultToast>
      )}

      <SwipeActions>
        <button className="no" onClick={() => onAnswer(false)}>← 아니오</button>
        <button className="yes" onClick={() => onAnswer(true)}>예 →</button>
      </SwipeActions>
    </>
  )
}


const statLabels: Array<[keyof TeamMember['baseStatsSnapshot'], string]> = [
  ['hp', 'HP'],
  ['atk', '공격'],
  ['def', '방어'],
  ['spa', '특공'],
  ['spd', '특방'],
  ['spe', '스피드'],
]

function CreatePokemonScreen({
  member,
  onBack,
  onUpdate,
}: {
  member: TeamMember
  onBack: () => void
  onUpdate: (patch: Partial<TeamMember>) => void
}) {
  function updateEv(stat: keyof TeamMember['evs'], value: number) {
    onUpdate({ evs: { ...member.evs, [stat]: value } })
  }

  function updateDex(value: number) {
    onUpdate({
      nationalDexNumber: value,
      imageAssets: value > 0 ? imageAssetsFromDex(value) : null,
    })
  }

  const previewMember = member.pokemonName ? member : { ...member, pokemonName: 'Garchomp', nationalDexNumber: 445, imageAssets: imageAssetsFromDex(445) }

  return (
    <>
      <Header>
        <HeaderCopy>
          <PageTitle>포켓몬 만들기</PageTitle>
          <PageSubtitle>엔트리에 저장할 실전 샘플</PageSubtitle>
        </HeaderCopy>
        <IconButton onClick={onBack}>×</IconButton>
      </Header>

      <CreateScroll>
        <FormHero>
          <PreviewTile>
            {artworkUrl(previewMember) ? (
              <PokemonArtwork src={artworkUrl(previewMember) ?? undefined} alt={previewMember.pokemonName} onError={(event) => handleImageError(event, previewMember)} />
            ) : (
              <PlusButton>+</PlusButton>
            )}
          </PreviewTile>
          <FieldGroup>
            <FieldLabel>
              포켓몬
              <TextField value={member.pokemonName} placeholder="예: Garchomp" onChange={(event) => onUpdate({ pokemonName: event.target.value, pokemonId: event.target.value.toLowerCase().replace(/\s+/g, '-') })} />
            </FieldLabel>
          </FieldGroup>
          <FieldGroup>
            <FieldLabel>
              Lv
              <TextField type="number" value={member.level} onChange={(event) => onUpdate({ level: Number(event.target.value) })} />
            </FieldLabel>
          </FieldGroup>
        </FormHero>

        <TypeChipRow>
          <SmallTypeChip color="#79d19d">드래곤</SmallTypeChip>
          <SmallTypeChip color="#a78bfa">땅</SmallTypeChip>
        </TypeChipRow>

        <TwoColumnFields>
          {[1, 2, 3, 4].map((index) => (
            <FieldLabel key={index}>
              기술 {index}
              <SelectLike type="button">기술 선택 <span>⌄</span></SelectLike>
            </FieldLabel>
          ))}
        </TwoColumnFields>

        <FullField>
          <FieldLabel>
            특성
            <SelectLike type="button">특성 선택 <span>⌄</span></SelectLike>
          </FieldLabel>
        </FullField>

        <FullField>
          <FieldLabel>
            지닌 물건
            <SelectLike type="button">지닌 물건 선택 <span>⌄</span></SelectLike>
          </FieldLabel>
        </FullField>

        <TwoColumnFields>
          <FieldLabel>
            성격
            <TextField value={member.nature} placeholder="Jolly" onChange={(event) => onUpdate({ nature: event.target.value })} />
          </FieldLabel>
          <FieldLabel>
            National Dex
            <TextField type="number" value={member.nationalDexNumber ?? ''} placeholder="445" onChange={(event) => updateDex(Number(event.target.value))} />
          </FieldLabel>
        </TwoColumnFields>

        <StatHeader>
          <span>스탯</span>
          <span>기본</span>
          <span>노력치(EV)</span>
          <span>성격</span>
          <span>합계</span>
        </StatHeader>
        {statLabels.map(([stat, label]) => {
          const base = member.baseStatsSnapshot[stat]
          const ev = member.evs[stat] ?? 0
          const natureBonus = stat === 'spe' ? 10 : 0
          const total = base + Math.floor(ev / 8) + natureBonus
          return (
            <StatRow key={stat}>
              <span>{label}</span>
              <StatValue>{base}</StatValue>
              <RangeWrap>
                <TinyRoundButton type="button" onClick={() => updateEv(stat, Math.max(0, ev - 4))}>−</TinyRoundButton>
                <input type="range" min="0" max="252" step="4" value={ev} onChange={(event) => updateEv(stat, Number(event.target.value))} />
                <TinyRoundButton type="button" onClick={() => updateEv(stat, Math.min(252, ev + 4))}>+</TinyRoundButton>
              </RangeWrap>
              <span>+{natureBonus}</span>
              <strong>{total}</strong>
            </StatRow>
          )
        })}
      </CreateScroll>

      <BottomAction>
        <Button variant="primary" onPress={onBack}>엔트리에 저장</Button>
      </BottomAction>
    </>
  )
}

function AppContent() {
  const [screen, setScreen] = useState<ScreenName>(() => (globalThis.location?.hash === '#create' ? 'create' : 'entry'))
  const [teamDraft, setTeamDraft] = useState<UserTeam>({
    teamName: 'main',
    format: 'pokemon_champions',
    members: Array.from({ length: 6 }, (_, index) => defaultMember(index + 1)),
  })
  const [selectedDifficulty, setSelectedDifficulty] = useState<Difficulty | null>('normal')
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [questionIndex, setQuestionIndex] = useState(0)
  const [lastResult, setLastResult] = useState<AnswerResult | null>(null)
  const [activeSlot, setActiveSlot] = useState(1)

  const teamQuery = useQuery({ queryKey: ['team'], queryFn: api.getTeam })
  const difficultiesQuery = useQuery({ queryKey: ['difficulties'], queryFn: api.getDifficulties })
  const generateQuiz = useMutation({
    mutationFn: api.generateQuestions,
    onSuccess: (data) => {
      setQuestions(data.questions)
      setQuestionIndex(0)
      setLastResult(null)
      setScreen('quiz')
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
  const activeMember = teamDraft.members.find((member) => member.slot === activeSlot) ?? teamDraft.members[0]

  function updateMember(slot: number, patch: Partial<TeamMember>) {
    setTeamDraft((team) => ({
      ...team,
      members: team.members.map((member) => (member.slot === slot ? { ...member, ...patch } : member)),
    }))
  }

  function openCreate(slot: number) {
    setActiveSlot(slot)
    setScreen('create')
  }

  function startQuiz(difficulty = selectedDifficulty ?? 'easy') {
    setSelectedDifficulty(difficulty)
    generateQuiz.mutate(difficulty)
  }

  async function answer(answerValue: boolean) {
    if (!currentQuestion || answerQuestion.isPending) return
    const result = await answerQuestion.mutateAsync({ id: currentQuestion.id, answer: answerValue })
    setLastResult(result)
    setQuestionIndex((index) => index + 1)
  }

  return (
    <Screen>
      <Phone>
        <PhoneContent>
          <StatusBar>
            <span>9:41</span>
            <Signal><span /><span /><span /><span /></Signal>
          </StatusBar>

          {screen === 'entry' && <EntryScreen teamDraft={teamDraft} onStart={() => setScreen('difficulty')} onOpenCreate={openCreate} />}
          {screen === 'create' && activeMember && (
            <CreatePokemonScreen
              member={activeMember}
              onBack={() => setScreen('entry')}
              onUpdate={(patch) => updateMember(activeSlot, patch)}
            />
          )}
          {screen === 'difficulty' && (
            <DifficultyScreen
              options={difficultiesQuery.data}
              selectedDifficulty={selectedDifficulty}
              onBack={() => setScreen('entry')}
              onSelect={setSelectedDifficulty}
              onStart={() => startQuiz(selectedDifficulty ?? 'easy')}
            />
          )}
          {screen === 'quiz' && (
            <QuizScreen
              difficulty={selectedDifficulty}
              currentQuestion={currentQuestion}
              questionIndex={questionIndex}
              total={questions.length}
              lastResult={lastResult}
              isLoading={generateQuiz.isPending}
              onAnswer={(value) => void answer(value)}
            />
          )}
        </PhoneContent>
      </Phone>
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
