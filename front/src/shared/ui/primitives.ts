import styled from '@emotion/styled'
import { theme } from '../styles/theme'

export const PageShell = styled.main`
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(216, 79, 42, 0.18), transparent 32rem),
    ${theme.color.page};
  color: ${theme.color.ink};
  font-family:
    'Noto Sans KR', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
`

export const ContentFrame = styled.div`
  width: min(1120px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 64px;
`

export const Panel = styled.section`
  background: ${theme.color.panel};
  border: 1px solid ${theme.color.line};
  border-radius: ${theme.radius.card};
  box-shadow: ${theme.shadow.card};
  padding: ${theme.space.lg};
`

export const Button = styled.button<{ tone?: 'primary' | 'yes' | 'no' | 'ghost' }>`
  border: 0;
  border-radius: ${theme.radius.control};
  padding: 12px 18px;
  font-weight: 800;
  cursor: pointer;
  color: ${({ tone }) => (tone === 'ghost' ? theme.color.ink : 'white')};
  background: ${({ tone }) => {
    if (tone === 'yes') return theme.color.yes
    if (tone === 'no') return theme.color.no
    if (tone === 'ghost') return theme.color.panelStrong
    return theme.color.primary
  }};
  box-shadow: ${theme.shadow.soft};

  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
`

export const Input = styled.input`
  width: 100%;
  box-sizing: border-box;
  border: 1px solid ${theme.color.line};
  border-radius: ${theme.radius.control};
  padding: 10px 12px;
  background: white;
  font: inherit;
`

export const SmallText = styled.p`
  color: ${theme.color.muted};
  line-height: 1.6;
`
