import React from "react"
import ProgressInline from "./ProgressInline"

interface CCReportProgressBarEntryProps {
  progress: number
  total: number
  label?: string
}

const CCReportProgressBarEntry = ({
  progress,
  total,
  label
}: CCReportProgressBarEntryProps) => {
  return <ProgressInline label={label} progress={progress} total={total} compact />
}

export default CCReportProgressBarEntry
