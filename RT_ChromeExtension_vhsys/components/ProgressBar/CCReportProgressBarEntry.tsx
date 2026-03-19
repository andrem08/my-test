import React from "react"
import styled from "styled-components"

const ProgressBarContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: start;
  align-items: start;
  width: 100%;
  padding: 1.4rem;
`

const ProgressElementsBar = styled.div`
  display: flex;
  justify-content: left;
  align-items: start;
  gap: 1rem;
  
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
    background-color: ${(props) =>
      props.value === props.max ? "#4caf50" : "#ffa726"};
    border-radius: 10px;
    transition:
      background-color 0.5s,
      width 0.3s ease-in-out;
  }

  &::-moz-progress-bar {
    background-color: ${(props) =>
      props.value === props.max ? "#4caf50" : "#ffa726"};
    border-radius: 10px;
  }
`

const PercentageSpan = styled.span`

  font-weight: bold;
  color: #333;
  min-width: 40px;
  text-align: right;
white-space: nowrap;
`

const LabelSpan = styled.span`
font-weight: bold;
  color: #333;
  min-width: 60px;
  text-align: left;

`

const CCReportProgressBarEntry = ({ progress, total, label }) => {
  if (total === 0) {
    return null
  }

  const percentage = Math.floor((progress / total) * 100)

  return (
    <ProgressBarContainer>
      <ProgressElementsBar>
        <LabelSpan>{label}</LabelSpan>
        <StyledProgress value={progress} max={total} />
        <PercentageSpan>( {percentage}% - {progress}/{total} )</PercentageSpan>
  
      </ProgressElementsBar>
    </ProgressBarContainer>
  )
}

export default CCReportProgressBarEntry
