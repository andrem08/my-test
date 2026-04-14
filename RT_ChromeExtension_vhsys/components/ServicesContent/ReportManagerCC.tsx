import React, { useContext, useState } from "react"
import styled from "styled-components"
import CCReportProgressBar from "~components/ProgressBar/CCReportProgressBar"
import ServiceStatus from "~components/ServiceStatus"
import { buildServerRoute } from "~components/env"
import {
    updateReportCCLastSixMonthsMultiThread,
    updateReportCCMultiThread,
} from "../../ExtensionLogic/VHSYS/updateReportCC"
import { primaryButtonStyles } from "~components/shared/styles"
import { DataContext } from "../../context/DataContext"

const ScopePanel = styled.div`
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
    margin-bottom: 0.25rem;
`

const ScopeHeader = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    flex-wrap: wrap;
`

const ScopeHint = styled.span`
    font-size: 0.78rem;
    color: #5b4638;
    font-weight: 700;
`

const ScopeToggle = styled.div`
    display: inline-flex;
    width: 100%;
    border: 1px solid #d8c5ae;
    border-radius: 999px;
    overflow: hidden;
    background: #f6efe6;
`

const ScopeButton = styled.button<{ $active: boolean }>`
    flex: 1;
    border: 0;
    padding: 0.72rem 0.9rem;
    font-weight: 800;
    font-size: 0.78rem;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
    background: ${({ $active }) => ($active ? "#f0c38a" : "transparent")};
    color: ${({ $active }) => ($active ? "#2f2218" : "#6f5a49")};

    &:hover:not(:disabled) {
        background: ${({ $active }) => ($active ? "#edb66f" : "rgba(242, 235, 226, 0.95)")};
        transform: translateY(-1px);
    }

    &:disabled {
        cursor: not-allowed;
        opacity: 0.72;
    }
`

const ResetButton = styled.button`
  ${primaryButtonStyles}
  min-width: 98px
  padding: 10px 14px
`

const RecentUpdateButton = styled.button`
    ${primaryButtonStyles}
    min-width: 188px
    padding: 10px 14px
`

export default function RelatorioManagerCC() {
    const context = useContext(DataContext)
    if (!context) return <p>Context not available</p>

    const { data, entries, outputs, total, ccReportScope, setCCReportScope } = context
    const [putLoading, setPutLoading] = useState<boolean>(false)

    const ccIsRunning = Array.isArray(data)
        ? data.some(
            (item) =>
                (item.ACTION === "CC_REPORT" || item.ACTION === "CC_REPORT_3_MONTHS")
                && item.RUN_STATUS === 1
        )
        : false

    const scopeLabel = ccReportScope === "last_3_months" ? "Ultimos 3 meses" : "Geral"

    const startCurrentScopeUpdate = () => {
        if (ccIsRunning) return

        const run = ccReportScope === "last_3_months"
            ? updateReportCCLastSixMonthsMultiThread(5, "CC_REPORT_3_MONTHS")
            : updateReportCCMultiThread(5, "CC_REPORT")

        void run.catch((error) => {
            console.error("Error updating CC report:", error)
        })
    }

    const handlePutReset = async () => {
        setPutLoading(true)
        try {
            const resetUrl = new URL(buildServerRoute('cc_report/reset'))
            resetUrl.searchParams.set('months_back', '3')

            const response = await fetch(resetUrl.toString(), {
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

            // Ao resetar, inicia automaticamente o update do escopo atual.
            startCurrentScopeUpdate()
        } catch (error) {
            console.error("Error with PUT request:", error)
        } finally {
            setPutLoading(false)
        }
    }

    const handleUpdateCurrentScope = () => {
        startCurrentScopeUpdate()
    }

    return (
        <ServiceStatus
            service="Relatorios de centro de custo"
            service_ref="CC_REPORT"
            showDefaultAction={false}
            actionSlot={
                <>
                    <RecentUpdateButton
                        onClick={handleUpdateCurrentScope}
                        disabled={ccIsRunning || putLoading}>
                        {ccIsRunning ? "Atualizando..." : "Atualizar"}
                    </RecentUpdateButton>
                    <ResetButton onClick={handlePutReset} disabled={putLoading || ccIsRunning}>
                        {putLoading ? "Resetando..." : "Resetar"}
                    </ResetButton>
                </>
            }>
            <ScopePanel>
                <ScopeHeader>
                    <ScopeHint>Visualizando: {scopeLabel}</ScopeHint>
                </ScopeHeader>

                <ScopeToggle>
                    <ScopeButton
                        type="button"
                        $active={ccReportScope === "all"}
                        onClick={() => setCCReportScope("all")}
                        disabled={putLoading || ccIsRunning}>
                        Geral
                    </ScopeButton>
                    <ScopeButton
                        type="button"
                        $active={ccReportScope === "last_3_months"}
                        onClick={() => setCCReportScope("last_3_months")}
                        disabled={putLoading || ccIsRunning}>
                        3 meses
                    </ScopeButton>
                </ScopeToggle>
            </ScopePanel>
            <CCReportProgressBar />
        </ServiceStatus>
    )
}
