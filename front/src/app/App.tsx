import { QueryClient, QueryClientProvider, useMutation, useQuery } from '@tanstack/react-query'
import { Button, Chip, Slider, Spinner } from '@heroui/react'
import styled from '@emotion/styled'
import { AnimatePresence, motion, useMotionValue, useTransform } from 'framer-motion'
import { useEffect, useState } from 'react'
import type { SyntheticEvent } from 'react'
import { api } from '../shared/api/client'
import type { Difficulty, DifficultyOption, QuizQuestion } from '../entities/quiz/types'
import type { TeamMember, UserTeam } from '../entities/team/types'

const queryClient = new QueryClient()

type ScreenName = 'entry' | 'difficulty' | 'generating' | 'quiz' | 'create' | 'complete' | 'review'

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
  padding: 12px 20px 18px;
  overflow: hidden;
`

const StatusBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 18px;
  margin-bottom: 6px;
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
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
`

const DifficultyBadge = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  background: #d8f8e6;
  color: #0a9f4b;
  font-size: 10px;
  font-weight: 1000;
`

const QuizPrompt = styled.div`
  text-align: center;
  margin-bottom: 22px;
`

const QuizTitle = styled.h1`
  margin: 8px auto 5px;
  max-width: 310px;
  font-size: 19px;
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
  position: relative;
  height: 318px;
  padding: 20px 15px 14px;
  overflow: hidden;
  border-radius: 24px;
  background: #ffffff;
  box-shadow: 0 20px 52px rgba(15, 23, 42, 0.10);
  touch-action: pan-y;
`

const SwipeGradient = styled(motion.div)<{ tone: 'yes' | 'no' }>`
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background: ${({ tone }) =>
    tone === 'yes'
      ? 'linear-gradient(235deg, rgba(23,201,100,0.30), rgba(23,201,100,0.06) 45%, rgba(255,255,255,0) 76%)'
      : 'linear-gradient(125deg, rgba(243,18,96,0.30), rgba(243,18,96,0.06) 45%, rgba(255,255,255,0) 76%)'};
  pointer-events: none;
`

const SwipeStamp = styled(motion.div)<{ tone: 'yes' | 'no' }>`
  position: absolute;
  top: 20px;
  ${({ tone }) => (tone === 'yes' ? 'right: 18px;' : 'left: 18px;')}
  z-index: 2;
  display: grid;
  place-items: center;
  min-width: 62px;
  height: 32px;
  border: 2px solid ${({ tone }) => (tone === 'yes' ? '#17C964' : '#F31260')};
  border-radius: 999px;
  color: ${({ tone }) => (tone === 'yes' ? '#17C964' : '#F31260')};
  background: rgba(255, 255, 255, 0.82);
  font-size: 13px;
  font-weight: 1000;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
  transform: rotate(${({ tone }) => (tone === 'yes' ? '10deg' : '-10deg')});
  pointer-events: none;
`

const QuizCardInner = styled.div`
  position: relative;
  z-index: 1;
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
  width: 84px;
  height: 84px;
  place-items: center;
  border-radius: 50%;
  background: #f7f8fa;
`

const QuizArtwork = styled.img`
  max-width: 88px;
  max-height: 78px;
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
  margin-top: 16px;
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

const LoadingLayer = styled.div`
  display: grid;
  min-height: 420px;
  place-items: center;
  color: #7b8089;
  font-size: 13px;
  font-weight: 800;
`

const GeneratingWrap = styled.div`
  position: relative;
  display: grid;
  min-height: calc(100% - 24px);
  grid-template-rows: 1fr auto;
  overflow: hidden;
  border-radius: 0 0 24px 24px;
  background:
    radial-gradient(circle at 50% -6%, #e6f1fe 0, rgba(230, 241, 254, 0.58) 34%, rgba(250, 250, 250, 0) 58%),
    #fafafa;
`

const GeneratingCenter = styled.div`
  display: grid;
  align-content: start;
  justify-items: center;
  gap: 14px;
  padding: 54px 0 32px;
  text-align: center;
`

const PokeballLoader = styled.div`
  position: relative;
  width: 76px;
  height: 76px;
  margin-bottom: 12px;
  border: 5px solid #111827;
  border-radius: 999px;
  background: linear-gradient(#ff1f63 0 48%, #111827 48% 55%, #ffffff 55% 100%);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.12);
  animation: pokeballSpin 1.4s linear infinite;

  &::before {
    content: '';
    position: absolute;
    left: 50%;
    top: 50%;
    width: 23px;
    height: 23px;
    border: 4px solid #111827;
    border-radius: 999px;
    background: #ffffff;
    transform: translate(-50%, -50%);
    box-shadow: inset 0 0 0 4px #dbe2ea;
  }

  @keyframes pokeballSpin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`

const LoadingDots = styled.div`
  display: flex;
  gap: 5px;
  margin-top: -7px;

  span {
    width: 5px;
    height: 5px;
    border-radius: 999px;
    background: #006fee;
    animation: dotBlink 1.1s ease-in-out infinite;
  }

  span:nth-of-type(2) { animation-delay: 0.15s; }
  span:nth-of-type(3) { animation-delay: 0.3s; }

  @keyframes dotBlink {
    0%, 80%, 100% { opacity: 0.28; transform: translateY(0); }
    40% { opacity: 1; transform: translateY(-3px); }
  }
`

const GeneratingTitle = styled.h1`
  margin: 0;
  color: #111827;
  font-size: 18px;
  line-height: 1.12;
  font-weight: 1000;
  letter-spacing: -0.06em;
`

const GeneratingCopy = styled.p`
  max-width: 220px;
  margin: -4px 0 0;
  color: #6b7280;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.45;
`

const IndeterminateTrack = styled.div`
  position: relative;
  width: 204px;
  height: 4px;
  margin: 2px 0 6px;
  overflow: hidden;
  border-radius: 999px;
  background: #e5e7eb;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -45%;
    width: 45%;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, rgba(0, 111, 238, 0), #006fee 45%, rgba(0, 111, 238, 0));
    animation: progressSlide 1.3s ease-in-out infinite;
  }

  @keyframes progressSlide {
    0% { transform: translateX(0); }
    100% { transform: translateX(330%); }
  }
`

const LoadingChecklist = styled.div`
  display: grid;
  gap: 12px;
  width: 230px;
  margin-top: 4px;
  text-align: left;
`

const LoadingStep = styled.div<{ state: 'done' | 'active' | 'pending' }>`
  display: grid;
  grid-template-columns: 18px 1fr;
  align-items: center;
  gap: 9px;
  color: ${({ state }) => (state === 'active' ? '#006fee' : state === 'done' ? '#374151' : '#9ca3af')};
  font-size: 11px;
  font-weight: 900;
`

const StepIcon = styled.span<{ state: 'done' | 'active' | 'pending' }>`
  display: grid;
  width: 16px;
  height: 16px;
  place-items: center;
  border-radius: 999px;
  border: 1.5px solid ${({ state }) => (state === 'done' ? '#17c964' : state === 'active' ? '#006fee' : '#d1d5db')};
  background: ${({ state }) => (state === 'done' ? '#17c964' : 'transparent')};
  color: #ffffff;
  font-size: 10px;
  line-height: 1;

  ${({ state }) => state === 'active' ? `
    border-top-color: transparent;
    animation: stepSpin 0.8s linear infinite;

    @keyframes stepSpin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  ` : ''}
`

const GeneratingFooter = styled.div`
  padding: 0 28px 8px;
  color: #6b7280;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.35;
  text-align: center;
`

const GeneratingError = styled.div`
  width: 230px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 61, 117, 0.09);
  color: #be123c;
  font-size: 11px;
  font-weight: 900;
  line-height: 1.45;
`

const ConfettiLayer = styled.div`
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
`

const ConfettiPiece = styled.span<{ left: number; delay: number; color: string }>`
  position: absolute;
  top: -24px;
  left: ${({ left }) => left}%;
  width: 7px;
  height: 13px;
  border-radius: 3px;
  background: ${({ color }) => color};
  opacity: 0.9;
  animation: confFall 2.8s linear infinite;
  animation-delay: ${({ delay }) => delay}s;

  @keyframes confFall {
    0% { transform: translateY(-28px) rotate(0deg); }
    100% { transform: translateY(900px) rotate(420deg); }
  }
`

const CompleteWrap = styled.div`
  position: relative;
  display: grid;
  height: calc(100% - 34px);
  grid-template-rows: 1fr auto;
  text-align: center;
`

const CompleteCenter = styled.div`
  display: grid;
  align-content: start;
  justify-items: center;
  gap: 12px;
  padding-top: 54px;
`

const MascotStage = styled.div`
  display: grid;
  justify-items: center;
  gap: 3px;
  margin-bottom: 4px;
`

const Mascot = styled.img`
  width: 104px;
  height: 104px;
  object-fit: contain;
  image-rendering: auto;
  filter: drop-shadow(0 18px 18px rgba(15, 23, 42, 0.18));
  animation: bob 1.15s ease-in-out infinite;

  @keyframes bob {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }
`

const MascotShadow = styled.div`
  width: 82px;
  height: 16px;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.13);
  filter: blur(1px);
  animation: shadowPulse 1.15s ease-in-out infinite;

  @keyframes shadowPulse {
    0%, 100% { transform: scaleX(1); opacity: 0.18; }
    50% { transform: scaleX(0.74); opacity: 0.09; }
  }
`

const CompleteTitle = styled.h1`
  margin: 0;
  font-size: 24px;
  line-height: 1.05;
  letter-spacing: -0.07em;
`

const CompleteSubtitle = styled.p`
  margin: 0;
  color: #71717a;
  font-size: 13px;
  font-weight: 800;
`

const BigScore = styled.div`
  display: flex;
  margin-top: 2px;
  align-items: baseline;
  gap: 5px;
  color: #111827;
  font-weight: 1000;

  strong {
    font-size: 48px;
    line-height: 1;
    letter-spacing: -0.08em;
  }

  span {
    color: #a1a1aa;
    font-size: 24px;
  }
`

const SummaryGrid = styled.div`
  display: grid;
  width: 100%;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 5px;
`

const SummaryCard = styled.div`
  padding: 11px 7px;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.055);

  span {
    display: block;
    color: #8a929d;
    font-size: 10px;
    font-weight: 900;
  }

  strong {
    display: block;
    margin-top: 4px;
    color: #111827;
    font-size: 18px;
    line-height: 1;
  }
`

const CompleteActions = styled.div`
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 16px;
  display: grid;
  gap: 8px;

  button {
    width: 100%;
    height: 42px;
    border-radius: 13px;
    font-weight: 900;
  }
`

const SoundButton = styled.button`
  border: 1px solid #e4e4e7;
  background: #ffffff;
  color: #3f3f46;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
`

const ReviewScroll = styled.div`
  height: calc(100% - 86px);
  overflow-y: auto;
  padding: 2px 2px 84px;
  scrollbar-width: none;

  &::-webkit-scrollbar { display: none; }
`

const ReviewHeader = styled(Header)`
  margin-bottom: 14px;
`

const ReviewCard = styled.article`
  display: grid;
  gap: 9px;
  margin-bottom: 10px;
  padding: 12px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.055);
`

const ReviewCardTop = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #71717a;
  font-size: 11px;
  font-weight: 1000;
`

const ScorePill = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 28px;
  border-radius: 999px;
  background: #111827;
  color: #ffffff;
  font-size: 11px;
  font-weight: 1000;
`

const ResultBadge = styled.span<{ correct: boolean }>`
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: ${({ correct }) => (correct ? '#e8faf0' : '#fff0f5')};
  color: ${({ correct }) => (correct ? '#17c964' : '#f31260')};
  font-size: 10px;
  font-weight: 1000;
`

const ReviewQuestion = styled.p`
  margin: 0;
  color: #111827;
  font-size: 14px;
  font-weight: 900;
  line-height: 1.35;
  letter-spacing: -0.04em;
`

const MiniMatchup = styled.div`
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 8px;
  align-items: center;
`

const MiniPokemon = styled.div`
  display: grid;
  justify-items: center;
  gap: 4px;
  min-width: 0;

  img {
    width: 48px;
    height: 48px;
    object-fit: contain;
  }

  strong {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 11px;
  }
`

const AnswerCompare = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
`

const AnswerBox = styled.div`
  padding: 9px;
  border-radius: 13px;
  background: #f7f8fa;
  color: #71717a;
  font-size: 10px;
  font-weight: 900;

  strong {
    display: block;
    margin-top: 4px;
    color: #111827;
    font-size: 13px;
  }
`

const ExplanationBox = styled.div`
  padding: 10px;
  border-radius: 14px;
  background: #fff8e8;
  color: #8a5b00;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.45;
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
  grid-template-columns: 74px minmax(0, 1fr);
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

  [data-slot='slider'] {
    flex: 1;
    min-width: 0;
  }

  [data-slot='slider-track'] {
    height: 6px;
    border-radius: 999px;
  }

  [data-slot='slider-fill'] {
    background: #0b7bf3;
  }

  [data-slot='slider-thumb'] {
    width: 14px;
    height: 14px;
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
const confettiColors = ['#006FEE', '#17C964', '#F31260', '#F5A524', '#A33EA1', '#63BC5A']

type QuizDraftAnswer = {
  question: QuizQuestion
  answer: boolean
}

type QuizSummary = {
  total: number
  correct: number
  wrong: number
  accuracy: number
}

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

function mockMember(slot: number, name: string, dex: number, baseSpeed: number): TeamMember {
  return {
    slot,
    pokemonId: name.toLowerCase().replace(/\s+/g, '-'),
    pokemonName: name,
    nationalDexNumber: dex,
    imageAssets: imageAssetsFromDex(dex),
    baseStatsSnapshot: { hp: 1, atk: 1, def: 1, spa: 1, spd: 1, spe: baseSpeed },
    level: 50,
    nature: 'Jolly',
    ability: null,
    item: null,
    evs: { spe: 252 },
    ivs: { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 },
  }
}

function makeMockQuestions(subject: TeamMember): QuizQuestion[] {
  const baseSubject = subject.pokemonName ? subject : mockMember(1, '한카리아스', 445, 102)
  const opponents = [
    mockMember(99, '무쇠손', 992, 50),
    mockMember(100, '드래펄트', 887, 142),
    mockMember(101, '망나뇽', 149, 80),
  ]

  return opponents.map((opponent, index) => {
    const subjectSpeed = baseSubject.baseStatsSnapshot.spe
    const opponentSpeed = opponent.baseStatsSnapshot.spe
    return {
      id: `mock-speed-preview-${index + 1}`,
      difficulty: 'easy',
      mode: 'IS_FASTER',
      statement: `내 ${baseSubject.pokemonName}가 ${opponent.pokemonName}보다 빠를까?`,
      answerType: 'YES_NO',
      correctAnswer: subjectSpeed > opponentSpeed,
      subject: {
        build: baseSubject,
        speed: { rawSpeed: subjectSpeed, effectiveSpeed: subjectSpeed, modifiers: [`base speed=${subjectSpeed}`] },
      },
      opponent: {
        build: opponent,
        speed: { rawSpeed: opponentSpeed, effectiveSpeed: opponentSpeed, modifiers: [`base speed=${opponentSpeed}`] },
      },
      explanation: `${baseSubject.pokemonName}: ${subjectSpeed}, ${opponent.pokemonName}: ${opponentSpeed}. ${subjectSpeed} ${subjectSpeed > opponentSpeed ? '>' : '<='} ${opponentSpeed} 이므로 정답은 ${subjectSpeed > opponentSpeed ? '예' : '아니오'}입니다.`,
      rulesetVersion: 'mock-preview',
    } satisfies QuizQuestion
  })
}

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

function animatedSpriteUrl(member: TeamMember): string | null {
  if (!member.nationalDexNumber || member.nationalDexNumber > 649) return artworkUrl(member)
  return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/${member.nationalDexNumber}.gif`
}

function handleMascotError(event: SyntheticEvent<HTMLImageElement>, member: TeamMember) {
  const fallback = artworkUrl(member)
  if (fallback && event.currentTarget.src !== fallback) {
    event.currentTarget.src = fallback
  }
}

function answerLabel(answer: boolean) {
  return answer ? '예' : '아니오'
}

function buildQuizSummary(answers: QuizDraftAnswer[]): QuizSummary {
  const correct = answers.filter((item) => item.answer === item.question.correctAnswer).length
  const total = answers.length
  return {
    total,
    correct,
    wrong: total - correct,
    accuracy: total ? Math.round((correct / total) * 100) : 0,
  }
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

function GeneratingQuizScreen({
  difficulty,
  isError,
  onBack,
  onRetry,
}: {
  difficulty: Difficulty | null
  isError: boolean
  onBack: () => void
  onRetry: () => void
}) {
  const label = difficulty ? difficultyTitle({ id: difficulty, label: difficulty, description: '' }) : '선택한 난이도'
  return (
    <GeneratingWrap>
      <GeneratingCenter>
        <PokeballLoader aria-label="퀴즈 생성 중" />
        <LoadingDots aria-hidden="true"><span /><span /><span /></LoadingDots>
        <GeneratingTitle>퀴즈 만드는 중</GeneratingTitle>
        <GeneratingCopy>
          내 엔트리와 메타 포켓몬을 비교해<br />최적의 문제를 생성하고 있어요
        </GeneratingCopy>
        <IndeterminateTrack aria-hidden="true" />
        <LoadingChecklist>
          <LoadingStep state="done"><StepIcon state="done">✓</StepIcon><span>메타 포켓몬 불러오는 중</span></LoadingStep>
          <LoadingStep state="done"><StepIcon state="done">✓</StepIcon><span>스피드 공식 계산 중</span></LoadingStep>
          <LoadingStep state="active"><StepIcon state="active" /><span>문제 만드는 중 · {label}</span></LoadingStep>
          <LoadingStep state="pending"><StepIcon state="pending" /><span>정답 · 해설 준비 중</span></LoadingStep>
        </LoadingChecklist>
        {isError && (
          <GeneratingError>
            문제 생성에 실패했어요. 서버 상태를 확인하거나 다시 시도해 주세요.
          </GeneratingError>
        )}
        {isError && <Button variant="primary" onPress={onRetry}>다시 생성하기</Button>}
      </GeneratingCenter>

      <GeneratingFooter>
        {isError ? '난이도 선택으로 돌아가려면 뒤로 가기를 눌러 주세요' : '잠시만 기다려 주세요 · 보통 몇 초면 끝나요'}
        <br />
        {!isError && <button type="button" onClick={onBack} style={{ marginTop: 6, border: 0, background: 'transparent', color: '#9ca3af', font: 'inherit', cursor: 'pointer' }}>난이도 다시 선택</button>}
      </GeneratingFooter>
    </GeneratingWrap>
  )
}

function QuizScreen({
  difficulty,
  currentQuestion,
  questionIndex,
  total,
  isLoading,
  onAnswer,
}: {
  difficulty: Difficulty | null
  currentQuestion: QuizQuestion | undefined
  questionIndex: number
  total: number
  isLoading: boolean
  onAnswer: (answer: boolean) => void
}) {
  const x = useMotionValue(0)
  const rotate = useTransform(x, [-180, 0, 180], [-7, 0, 7])
  const yesOpacity = useTransform(x, [18, 115], [0, 1])
  const noOpacity = useTransform(x, [-115, -18], [1, 0])
  const yesScale = useTransform(x, [18, 115], [0.92, 1.06])
  const noScale = useTransform(x, [-115, -18], [1.06, 0.92])

  return (
    <>
      <QuizTop>
        <DifficultyBadge>{difficulty ? difficultyTitle({ id: difficulty, label: difficulty, description: '' }) : '쉬움'}</DifficultyBadge>
        <PageSubtitle style={{ justifySelf: 'end' }}>{Math.min(questionIndex + 1, total || 1)} / {total || 5}</PageSubtitle>
      </QuizTop>

      <QuizPrompt>
        <QuizTitle>{currentQuestion?.statement ?? '내 포켓몬이 메타 샘플보다 빠를까?'}</QuizTitle>
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
            style={{ x, rotate }}
            dragElastic={0.16}
            dragConstraints={{ left: 0, right: 0 }}
            onDragEnd={(_, info) => {
              if (info.offset.x > 100) {
                onAnswer(true)
                return
              }
              if (info.offset.x < -100) {
                onAnswer(false)
              }
            }}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96 }}
          >
            <SwipeGradient tone="no" style={{ opacity: noOpacity }} />
            <SwipeGradient tone="yes" style={{ opacity: yesOpacity }} />
            <SwipeStamp tone="no" style={{ opacity: noOpacity, scale: noScale }}>아니오 ✕</SwipeStamp>
            <SwipeStamp tone="yes" style={{ opacity: yesOpacity, scale: yesScale }}>예 ✓</SwipeStamp>
            <QuizCardInner>
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
            </QuizCardInner>
          </QuizCard>
        </AnimatePresence>
      )}

      {!isLoading && total > 0 && !currentQuestion && <LoadingLayer>이번 세트 완료!</LoadingLayer>}


      <SwipeActions>
        <button className="no" onClick={() => onAnswer(false)}>← 아니오</button>
        <button className="yes" onClick={() => onAnswer(true)}>예 →</button>
      </SwipeActions>
    </>
  )
}


function playChime() {
  const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AudioContextCtor) return
  const ctx = new AudioContextCtor()
  ;[523.25, 659.25, 783.99, 1046.5].forEach((frequency, index) => {
    const oscillator = ctx.createOscillator()
    const gain = ctx.createGain()
    oscillator.type = 'triangle'
    oscillator.frequency.value = frequency
    oscillator.connect(gain)
    gain.connect(ctx.destination)
    const time = ctx.currentTime + index * 0.11
    gain.gain.setValueAtTime(0, time)
    gain.gain.linearRampToValueAtTime(0.2, time + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0008, time + 0.32)
    oscillator.start(time)
    oscillator.stop(time + 0.34)
  })
}

function CompleteScreen({ answers, mascot, onReview, onHome }: { answers: QuizDraftAnswer[]; mascot: TeamMember; onReview: () => void; onHome: () => void }) {
  const summary = buildQuizSummary(answers)
  const mascotSrc = animatedSpriteUrl(mascot) ?? artworkUrl(mascot) ?? undefined
  const mascotName = mascot.pokemonName || '포켓몬'

  return (
    <CompleteWrap>
      <ConfettiLayer aria-hidden="true">
        {Array.from({ length: 26 }, (_, index) => (
          <ConfettiPiece key={index} left={(index * 17) % 100} delay={-(index % 8) * 0.22} color={confettiColors[index % confettiColors.length]} />
        ))}
      </ConfettiLayer>
      <CompleteCenter>
        <MascotStage>
          {mascotSrc && <Mascot src={mascotSrc} alt={mascotName} onError={(event) => handleMascotError(event, mascot)} />}
          <MascotShadow />
        </MascotStage>
        <div>
          <CompleteTitle>퀴즈 완료!</CompleteTitle>
          <CompleteSubtitle>{mascotName}와 함께 완주했어요</CompleteSubtitle>
        </div>
        <BigScore>
          <strong>{summary.correct}</strong>
          <span>/ {summary.total || 0}</span>
        </BigScore>
        <SummaryGrid>
          <SummaryCard><span>정답</span><strong>{summary.correct}</strong></SummaryCard>
          <SummaryCard><span>오답</span><strong>{summary.wrong}</strong></SummaryCard>
          <SummaryCard><span>정답률</span><strong>{summary.accuracy}%</strong></SummaryCard>
        </SummaryGrid>
      </CompleteCenter>
      <CompleteActions>
        <SoundButton type="button" onClick={playChime}>🔊 완료 효과음 듣기</SoundButton>
        <Button variant="primary" onPress={summary.total ? onReview : onHome}>{summary.total ? '정답 & 해설 보기' : '홈으로'}</Button>
      </CompleteActions>
    </CompleteWrap>
  )
}

function ReviewScreen({ answers, onHome }: { answers: QuizDraftAnswer[]; onHome: () => void }) {
  const summary = buildQuizSummary(answers)
  return (
    <>
      <ReviewHeader>
        <IconButton onClick={onHome}>‹</IconButton>
        <HeaderCopy>
          <PageTitle>정답 & 해설</PageTitle>
        </HeaderCopy>
        <ScorePill>{summary.correct}/{summary.total}</ScorePill>
      </ReviewHeader>

      <ReviewScroll>
        {answers.map((item, index) => {
          const correct = item.answer === item.question.correctAnswer
          return (
            <ReviewCard key={`${item.question.id}-${index}`}>
              <ReviewCardTop>
                <span>문제 {String(index + 1).padStart(2, '0')}</span>
                <ResultBadge correct={correct}>{correct ? '✓ 정답' : '✕ 오답'}</ResultBadge>
              </ReviewCardTop>
              <ReviewQuestion>{item.question.statement}</ReviewQuestion>
              <MiniMatchup>
                <MiniPokemon>
                  <img src={artworkUrl(item.question.subject.build) ?? undefined} alt={item.question.subject.build.pokemonName} onError={(event) => handleImageError(event, item.question.subject.build)} />
                  <strong>{item.question.subject.build.pokemonName}</strong>
                </MiniPokemon>
                <VersusBadge style={{ marginTop: 0, width: 28, height: 28, fontSize: 10 }}>VS</VersusBadge>
                <MiniPokemon>
                  <img src={artworkUrl(item.question.opponent.build) ?? undefined} alt={item.question.opponent.build.pokemonName} onError={(event) => handleImageError(event, item.question.opponent.build)} />
                  <strong>{item.question.opponent.build.pokemonName}</strong>
                </MiniPokemon>
              </MiniMatchup>
              <AnswerCompare>
                <AnswerBox>내 답<strong>{answerLabel(item.answer)}</strong></AnswerBox>
                <AnswerBox>정답<strong>{answerLabel(item.question.correctAnswer)}</strong></AnswerBox>
              </AnswerCompare>
              <ExplanationBox>💡 {item.question.explanation}</ExplanationBox>
            </ReviewCard>
          )
        })}
      </ReviewScroll>

      <BottomAction>
        <Button variant="primary" onPress={onHome}>홈으로</Button>
      </BottomAction>
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
                <Slider
                  aria-label={`${label} EV`}
                  minValue={0}
                  maxValue={252}
                  step={4}
                  value={ev}
                  onChange={(value) => updateEv(stat, Array.isArray(value) ? value[0] : value)}
                >
                  <Slider.Track>
                    <Slider.Fill />
                    <Slider.Thumb />
                  </Slider.Track>
                </Slider>
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
  const [screen, setScreen] = useState<ScreenName>(() => {
    if (globalThis.location?.hash === '#create') return 'create'
    if (globalThis.location?.hash === '#generating') return 'generating'
    if (globalThis.location?.hash === '#quiz') return 'quiz'
    if (globalThis.location?.hash === '#complete') return 'complete'
    if (globalThis.location?.hash === '#review') return 'review'
    return 'entry'
  })
  const [teamDraft, setTeamDraft] = useState<UserTeam>({
    teamName: 'main',
    format: 'pokemon_champions',
    members: Array.from({ length: 6 }, (_, index) => defaultMember(index + 1)),
  })
  const [selectedDifficulty, setSelectedDifficulty] = useState<Difficulty | null>('normal')
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [questionIndex, setQuestionIndex] = useState(0)
  const [quizAnswers, setQuizAnswers] = useState<QuizDraftAnswer[]>([])
  const [activeSlot, setActiveSlot] = useState(1)

  const teamQuery = useQuery({ queryKey: ['team'], queryFn: api.getTeam })
  const difficultiesQuery = useQuery({ queryKey: ['difficulties'], queryFn: api.getDifficulties })
  const generateQuiz = useMutation({
    mutationFn: api.generateQuestions,
    onSuccess: (data) => {
      setQuestions(data.questions)
      setQuestionIndex(0)
      setQuizAnswers([])
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

  const activeMember = teamDraft.members.find((member) => member.slot === activeSlot) ?? teamDraft.members[0]
  const previewQuestions = makeMockQuestions(teamDraft.members[0] ?? defaultMember(1))
  const sessionQuestions = questions.length ? questions : previewQuestions
  const effectiveAnswers = quizAnswers.length ? quizAnswers : (screen === 'complete' || screen === 'review' ? previewQuestions.map((question, index) => ({ question, answer: index === 1 ? true : question.correctAnswer })) : [])
  const currentQuestion = sessionQuestions[questionIndex] ?? (screen === 'quiz' ? sessionQuestions[0] : undefined)
  const mascot = teamDraft.members.find((member) => member.pokemonName) ?? defaultMember(1)

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
    setQuizAnswers([])
    setQuestionIndex(0)
    setQuestions([])
    setScreen('generating')
    generateQuiz.mutate(difficulty)
  }

  function answer(answerValue: boolean) {
    if (!currentQuestion || answerQuestion.isPending) return

    const nextAnswers = [...quizAnswers, { question: currentQuestion, answer: answerValue }]
    setQuizAnswers(nextAnswers)

    if (questionIndex >= sessionQuestions.length - 1) {
      setScreen('complete')
      return
    }

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
          {screen === 'generating' && (
            <GeneratingQuizScreen
              difficulty={selectedDifficulty}
              isError={generateQuiz.isError}
              onBack={() => setScreen('difficulty')}
              onRetry={() => startQuiz(selectedDifficulty ?? 'easy')}
            />
          )}
          {screen === 'quiz' && (
            <QuizScreen
              difficulty={selectedDifficulty}
              currentQuestion={currentQuestion}
              questionIndex={questionIndex}
              total={sessionQuestions.length}
              isLoading={generateQuiz.isPending}
              onAnswer={(value) => void answer(value)}
            />
          )}
          {screen === 'complete' && <CompleteScreen answers={effectiveAnswers} mascot={mascot} onReview={() => setScreen('review')} onHome={() => setScreen('entry')} />}
          {screen === 'review' && <ReviewScreen answers={effectiveAnswers} onHome={() => setScreen('entry')} />}
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
