import React, { useEffect, useMemo, useState } from "react"

import ServiceStatus from "../ServiceStatus"

export default function ServiceNF() {
  return (
    <div>
      <ServiceStatus service="NF de Serviço" service_ref="SERVICE_NF_MANAGER" />
    </div>
  )
}
