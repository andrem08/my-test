import React, { useContext, useState } from "react"
import styled from "styled-components"
import CCReportProgressBar from "~components/ProgressBar/CCReportProgressBar"
import ServiceStatus from "~components/ServiceStatus"
import { buildServerRoute } from "~components/env"
import { primaryButtonStyles } from "~components/shared/styles"
import { DataContext } from "../../context/DataContext"

const ResetButton = styled.button`
  ${primaryButtonStyles}
  min-width: 98px
  padding: 10px 14px
`

export default function RelatorioManagerCC() {
    const context = useContext(DataContext)
    if (!context) return <p>Context not available</p>

    const { entries, outputs, total } = context
    const [putLoading, setPutLoading] = useState<boolean>(false)

    const handlePutReset = async () => {
        setPutLoading(true)
        try {
            const response = await fetch(buildServerRoute('cc_report/reset'), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ entries, outputs, total }),
            })
            if (!response.ok) {
                throw new Error('Failed to execute PUT request')
            }
            await response.json()
        } catch (error) {
            console.error("Error with PUT request:", error)
        } finally {
            setPutLoading(false)
        }
    }

    return (
        <ServiceStatus
            service="Relatorios de centro de custo"
            service_ref="CC_REPORT"
            actionSlot={
                <ResetButton onClick={handlePutReset} disabled={putLoading}>
                    {putLoading ? "Resetando..." : "Resetar"}
                </ResetButton>
            }>
            <CCReportProgressBar />
        </ServiceStatus>
    )
}
