import React, { useMemo, useState } from "react"
import styled from "styled-components"

import { cardStyles, primaryButtonStyles } from "./shared/styles"

const WORKFLOW_PRINCIPAL_WEBHOOK_URL =
  "https://n8n.srv1252717.hstgr.cloud/webhook/681fc287-d331-49c8-acdb-3b504e298db5"

const WORKFLOW_ACTIONS: Record<FlowMode, { label: string }> = {
  full: { label: "Rodar fluxo inteiro" },
  monthly: { label: "Rodar fluxo mensal" }
}

const Card = styled.section`
  ${cardStyles};
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0.85rem;
  margin-bottom: 0.8rem;
  text-align: left;
  width: 100%;

  @media (min-width: 900px) {
    padding: 1rem 1.05rem;
  }
`

const Title = styled.h4`
  margin: 0;
  font-size: 0.92rem;
  font-family: "Sora", "Manrope", sans-serif;
  color: #2f2118;
`

const Subtitle = styled.p`
  margin: 0;
  font-size: 0.78rem;
  color: #6f5a47;
`

const ButtonsRow = styled.div`
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;

  @media (min-width: 720px) {
    flex-wrap: nowrap;
  }
`

const WorkflowButton = styled.button`
  ${primaryButtonStyles};
  flex: 1 1 0;
  min-width: 150px;
  padding: 9px 12px;
  font-size: 12px;
`

const StatusText = styled.p<{ $isError?: boolean }>`
  margin: 0;
  font-size: 0.75rem;
  color: ${({ $isError }) => ($isError ? "#a21515" : "#5d4a39")};
`

type FlowMode = "full" | "monthly"

export default function ApiPopulateWorkflows() {
  const [running, setRunning] = useState<FlowMode | null>(null)
  const [statusMessage, setStatusMessage] = useState<string>("")
  const [statusIsError, setStatusIsError] = useState(false)

  const buttonLabel = useMemo(
    () => ({
      full: running === "full" ? "Rodando..." : WORKFLOW_ACTIONS.full.label,
      monthly:
        running === "monthly" ? "Rodando..." : WORKFLOW_ACTIONS.monthly.label
    }),
    [running]
  )

  const handleRun = async (mode: FlowMode) => {
    setRunning(mode)
    setStatusIsError(false)
    setStatusMessage("Iniciando workflow principal...")

    try {
      const response = await fetch(
        `${WORKFLOW_PRINCIPAL_WEBHOOK_URL}?mode=${mode}`,
        {
          method: "GET"
        }
      )

      if (!response.ok) {
        throw new Error(`Falha HTTP ${response.status}`)
      }

      setStatusMessage(
        mode === "full"
          ? "Fluxo inteiro iniciado com sucesso."
          : "Fluxo mensal iniciado com sucesso."
      )
    } catch (error) {
      console.error("Erro ao iniciar workflow:", error)
      setStatusIsError(true)
      setStatusMessage("Nao foi possivel iniciar o workflow. Verifique a rota configurada.")
    } finally {
      setRunning(null)
    }
  }

  return (
    <Card>
      <Title>Populacao de APIs</Title>
      <Subtitle>Dispare os fluxos de carga de dados no servidor.</Subtitle>

      <ButtonsRow>
        <WorkflowButton
          onClick={() => handleRun("full")}
          disabled={running !== null}
          aria-label="Rodar fluxo inteiro de populacao de APIs">
          {buttonLabel.full}
        </WorkflowButton>

        <WorkflowButton
          onClick={() => handleRun("monthly")}
          disabled={running !== null}
          aria-label="Rodar fluxo mensal de populacao de APIs">
          {buttonLabel.monthly}
        </WorkflowButton>
      </ButtonsRow>

      {statusMessage ? <StatusText $isError={statusIsError}>{statusMessage}</StatusText> : null}
    </Card>
  )
}
