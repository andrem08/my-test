import React, { useContext } from "react"
import styled from "styled-components"
import { DataContext } from "../../context/DataContext"


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
  font-family: sans-serif;
  font-weight: bold;
  color: #333;
  min-width: 40px;
  text-align: right;
white-space: nowrap;
`


/* trunk-ignore(eslint/react/prop-types) */
const CCReportProgressBarEntry = ({ progress, total }) => {
  if (total === 0) {
    return null
  }

  const percentage = Math.floor((progress / total) * 100)

  return (
    <ProgressBarContainer>
      <ProgressElementsBar>
   
        <StyledProgress value={progress} max={total} />
        <PercentageSpan>{percentage}% </PercentageSpan>
  
      </ProgressElementsBar>
    </ProgressBarContainer>
  )
}


const CCReportProgressBarTotal = () => {
  const context = useContext(DataContext)
  if (!context) return <p>Context not available</p>

  const { entries, outputs, total } = context

  if (total === 0) {
    return null
  }

  return (
    <ProgressBarContainer>
      <CCReportProgressBarEntry progress={(entries + outputs)} total={total*2}  /> 


   
    </ProgressBarContainer>
  )
}

export default CCReportProgressBarTotal
