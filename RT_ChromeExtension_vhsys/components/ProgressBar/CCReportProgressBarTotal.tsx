import React, { useContext } from "react"
import { DataContext } from "../../context/DataContext"
import ProgressInline from "./ProgressInline"


const CCReportProgressBarTotal = () => {
  const context = useContext(DataContext)
  if (!context) return <p>Context not available</p>

  const { entries, outputs, total } = context

  if (total === 0) {
    return null
  }

  return (
    <ProgressInline
      label="Total"
      progress={entries + outputs}
      total={total * 2}
      compact
    />
  )
}

export default CCReportProgressBarTotal
