import React, { useContext } from "react"
import { DataContext } from "../../context/DataContext"
import ProgressInline from "./ProgressInline"


const CCReportProgressBarTotal = () => {
  const context = useContext(DataContext)
  if (!context) return <p>Context not available</p>

  const { ccSummaryEntries, ccSummaryOutputs, ccSummaryTotal } = context

  if (ccSummaryTotal === 0) {
    return null
  }

  return (
    <ProgressInline
      label="Total"
      progress={ccSummaryEntries + ccSummaryOutputs}
      total={ccSummaryTotal * 2}
      compact
    />
  )
}

export default CCReportProgressBarTotal
