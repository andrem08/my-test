import React, { useContext } from "react"
import styled from "styled-components"
import { DataContext } from "../../context/DataContext"
import CCReportProgressBarEntry from "./CCReportProgressBarEntry"

const ProgressBarContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  width: 100%;
  padding: 0.25rem 0;
`

const CCReportProgressBar = () => {
  const context = useContext(DataContext)
  if (!context) return <p>Context not available</p>

  const { entries, outputs, total } = context

  if (total === 0) {
    return null
  }

  return (
    <ProgressBarContainer>
      <CCReportProgressBarEntry progress={entries} total={total} label="Entradas" />
      <CCReportProgressBarEntry progress={outputs} total={total} label="Saídas" />
    </ProgressBarContainer>
  )
}

export default CCReportProgressBar
