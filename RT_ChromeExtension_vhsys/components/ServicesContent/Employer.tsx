import React from "react"

import EmployerProgressBar from "~components/ProgressBar/EmployerProgressBar"

import ServiceStatus from "../ServiceStatus"

export default function Employer() {
  return (
    <div>
      <ServiceStatus
        service="Dados de funcionario"
        service_ref="EMPLOYERS"
        progressBar={<EmployerProgressBar />}></ServiceStatus>
    </div>
  )
}
