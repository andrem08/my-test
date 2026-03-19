import React, { useContext } from "react"
import styled from "styled-components"
import { DataContext } from "../../context/DataContext"
import CCReportProgressBarEntry from "./CCReportProgressBarEntry"

const ProgressBarContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 1.4rem;
    font-family: Poppins;
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
      <div>    <CCReportProgressBarEntry progress={entries} total={total} label="Entradas" />  </div>
  <div>   <CCReportProgressBarEntry progress={outputs} total={total} label="Saídas" />  </div>
  <div>
{/* <CCReportProgressBarTotal/> */}

  </div>
   
    </ProgressBarContainer>
  )
}

export default CCReportProgressBar
