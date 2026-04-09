import React from "react"
import styled from "styled-components"

interface ProgressInlineProps {
  label?: string
  progress: number
  total: number
  compact?: boolean
}

const ProgressBarContainer = styled.div<{ $compact?: boolean }>`
  display: flex;
  width: 100%;
  padding: ${({ $compact }) => ($compact ? "0.35rem 0" : "0.8rem 0")};
`

const ProgressElementsBar = styled.div`
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
  width: 100%;
`

const Label = styled.span`
  font-size: 0.78rem;
  font-weight: 700;
  color: #4f3b2f;
  min-width: 62px;
`

const StyledProgress = styled.progress`
  appearance: none;
  width: 150px;
  max-width: 100%;
  height: 0.72rem;
  border: 1px solid #d8c5ae;
  border-radius: 999px;
  overflow: hidden;

  &::-webkit-progress-bar {
    background-color: #f2ebe2;
    border-radius: 999px;
  }

  &::-webkit-progress-value {
    background-color: ${(props) =>
      props.value === props.max ? "#2f9b55" : "#f4a13c"};
    border-radius: 999px;
    transition: background-color 0.3s ease, width 0.2s ease-in-out;
  }

  &::-moz-progress-bar {
    background-color: ${(props) =>
      props.value === props.max ? "#2f9b55" : "#f4a13c"};
    border-radius: 999px;
  }
`

const Percentage = styled.span`
  font-size: 0.78rem;
  font-weight: 700;
  color: #3e2e22;
  min-width: 60px;
  white-space: nowrap;
`

const ProgressInline = ({ label, progress, total, compact }: ProgressInlineProps) => {
  if (total <= 0) {
    return null
  }

  const safeProgress = Math.max(0, Math.min(progress, total))
  const percentage = Math.floor((safeProgress / total) * 100)

  return (
    <ProgressBarContainer $compact={compact}>
      <ProgressElementsBar>
        {label ? <Label>{label}</Label> : null}
        <StyledProgress value={safeProgress} max={total} />
        <Percentage>
          {percentage}% ({safeProgress}/{total})
        </Percentage>
      </ProgressElementsBar>
    </ProgressBarContainer>
  )
}

export default ProgressInline
