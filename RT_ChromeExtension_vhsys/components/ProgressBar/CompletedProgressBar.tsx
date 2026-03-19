import React from "react"
import styled from "styled-components"

const ProgressBarContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 1.4rem;
`

const ProgressElementsBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  width: 80%;
`

const StyledProgress = styled.progress`
  appearance: none;
  width: 120px;
  height: 1rem;
  border: 1px solid #ccc;
  border-radius: 10px;
  overflow: hidden;

  &::-webkit-progress-bar {
    background-color: #f0f0f0;
    border-radius: 10px;
  }

  &::-webkit-progress-value {
    background-color: #4caf50; /* Green for completed */
    border-radius: 10px;
  }

  &::-moz-progress-bar {
    background-color: #4caf50; /* Green for completed */
    border-radius: 10px;
  }
`

const PercentageSpan = styled.span`
  font-family: sans-serif;
  font-weight: bold;
  color: #333;
  min-width: 40px;
  text-align: right;
`

const CompletedProgressBar = () => {
  return (
    <ProgressBarContainer>
      <ProgressElementsBar>
        <StyledProgress value={100} max={100} />
        <PercentageSpan>100%</PercentageSpan>
      </ProgressElementsBar>
    </ProgressBarContainer>
  )
}

export default CompletedProgressBar
