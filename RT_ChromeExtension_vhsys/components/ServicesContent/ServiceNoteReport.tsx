import React, { useEffect, useMemo, useState } from "react"

import ServiceStatus from "../ServiceStatus"

export default function ServicesNoteReport() {
  return (
    <div>
      <ServiceStatus
        service="Relatorio de notas serviço"
        service_ref="SERVICE_NF"
      />
    </div>
  )
}
