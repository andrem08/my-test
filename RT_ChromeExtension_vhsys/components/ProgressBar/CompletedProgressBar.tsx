import React from "react"
import ProgressInline from "./ProgressInline"

const CompletedProgressBar = () => {
  return <ProgressInline label="Concluído" progress={100} total={100} compact />
}

export default CompletedProgressBar
