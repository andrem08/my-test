import React, { useContext, useEffect, useState } from "react"
import { BiSolidDownArrow, BiSolidUpArrow } from "react-icons/bi"
import styled from "styled-components"
import LoadingAnimation from "~components/Loading"
import { updated_version } from "~/version"
import RegularBillsProgressBar from "~components/ProgressBar/RegularBillsProgressBar"
import EmployerProgressBar from "~components/ProgressBar/EmployerProgressBar"
import ApiPopulateWorkflows from "~components/ApiPopulateWorkflows"
import ResetButton from "~components/ResetButton"
import RegularBills from "~components/ServicesContent/RegularBills"
import RelatorioManagerCC from "~components/ServicesContent/ReportManagerCC"
import StatusIcon from "~components/StatusIcon"
import CCReportProgressBarTotal from "./ProgressBar/CCReportProgressBarTotal"
import { DataContext } from "../context/DataContext"
import Employer from "./ServicesContent/Employer"
import SalesNF from "./ServicesContent/SalesNF"
import ServiceNF from "./ServicesContent/ServiceNF"
import ServicesNoteReport from "./ServicesContent/ServiceNoteReport"
import { primaryButtonStyles } from "./shared/styles"

const CommandGroupHeader = styled.div`
  padding: 0.9rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  box-shadow: rgba(17, 12, 46, 0.15) 0px 48px 100px 0px;
  width: 100%;

  @media (min-width: 900px) {
    padding: 1rem 1.1rem;
  }

  h3 {
    margin: auto 0;
    color: gray;
    font-weight: 600;
  }
  button {
    margin: auto 0 auto auto;
    padding: 1em;
    background: none;
    border: none;
    outline: none;
    font-size: 1rem;
  }
`
const CommandGroupHeaderDisabled = styled.div`
  padding: 0.9rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  box-shadow: rgba(17, 12, 46, 0.15) 0px 48px 100px 0px;
  background-color: aliceblue;
  opacity: 0.5;
  width: 100%;

  @media (min-width: 900px) {
    padding: 1rem 1.1rem;
  }

  h3 {
    margin: auto 0;
    color: gray;
    font-weight: 600;
  }
  button {
    margin: auto 0 auto auto;
    padding: 1em;
    background: none;
    border: none;
    outline: none;
    font-size: 1rem;
  }
`
const CommandGroupList = styled.div`
  display: flex;
  flex-direction: column;
  border-radius: 0 0 14px 14px;
  border: 1px solid rgba(115, 86, 58, 0.16);
  border-top: none;
  background: linear-gradient(180deg, rgba(244, 235, 225, 0.68) 0%, rgba(236, 226, 215, 0.78) 100%);
  transition: 0.25s ease;
  padding: 0.75rem;
  width: 100%;
`
const Container = styled.div`
  text-align: center;
  padding: 0.85rem;
  width: min(100%, 980px);
  min-width: 320px;
  margin: 0 auto;

  @media (min-width: 900px) {
    padding: 1rem 1.15rem 1.25rem;
  }
`

const StatusBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
`
const ProgressBarAlign = styled.div`
padding-right: 0.5rem;
  display: flex;
  align-items: center;
  padding-right: 0.5rem;
`
const ContainerHeader = styled.div`
  display: flex;
  flex-direction: column;
  padding-top: 1.2rem;
  text-align: center;
  padding-bottom: 1.2rem;

  h1 {
    font-size: 1.5rem;
  }
  img {
    width: min(148px, 50vw);
    margin: 0 auto;
  }

  @media (min-width: 900px) {
    padding-top: 1.5rem;
    padding-bottom: 1.4rem;

    h1 {
      font-size: 1.65rem;
    }
  }
`

const ReloadButton = styled.button`
  ${primaryButtonStyles}
  margin: 0.9rem auto 0;
  min-width: 132px;
  padding: 10px 14px;
`
const ItemHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0rem 1rem;

  h3 {
    min-width: 0;
  }

  @media (max-width: 520px) {
    flex-direction: column;
    align-items: flex-start;
  }
`
function isAnyJobRunning(jobs: any[]): boolean {
  return jobs.some((job) => job.RUN_STATUS === 1)
}

interface ServiceDataItem {
  ACTION: string
  RUN_STATUS: number
}

interface AccordionItemProps {
  name: string
  content: React.ReactNode
  data: ServiceDataItem[]
  serviceRef: string
  progressBar?: React.ReactNode
}

import CompletedProgressBar from "./ProgressBar/CompletedProgressBar"

import ServiceNFProgressBar from "./ProgressBar/ServiceNFProgressBar"

const AccordionItem: React.FC<AccordionItemProps> = ({
  name,
  content,
  data,
  serviceRef,
  progressBar
}) => {
  const ItemsStatus = data.find(
    (service: { ACTION: string }) => service.ACTION.trim() === serviceRef.trim()
  )
  const [hidden, setHidden] = useState(true)
  const currentStatus = ItemsStatus ? ItemsStatus.RUN_STATUS : 0
  const anyJobRunning = isAnyJobRunning(data)
  const isThisJobRunning = currentStatus === 1
  const isCompleted = currentStatus === 2
  const isDisabled = anyJobRunning && !isThisJobRunning
  if (isDisabled) {
    return (
      <div>
        <CommandGroupHeaderDisabled>
          <ItemHeader>
            <h3>{name}</h3>

            <StatusIcon status={currentStatus} />
          </ItemHeader>
          <button disabled>
            <BiSolidDownArrow />
          </button>
        </CommandGroupHeaderDisabled>
      </div>
    )
  }
  return (
    <div>
      <CommandGroupHeader>
        <ItemHeader>
          <h3>{name} </h3>
          <StatusBar>
            <ProgressBarAlign>
              {isCompleted ? <CompletedProgressBar /> : progressBar}
            </ProgressBarAlign>
            <StatusIcon status={currentStatus} />
          </StatusBar>

        </ItemHeader>
        <button onClick={() => setHidden(!hidden)}>
          {hidden ? <BiSolidDownArrow /> : <BiSolidUpArrow />}
        </button>
      </CommandGroupHeader>
      {!hidden && <CommandGroupList>{content}</CommandGroupList>}
    </div>
  )
}
function IndexPopup() {
  const context = useContext(DataContext)
  const [isOnCorrectPage, setIsOnCorrectPage] = useState<boolean | null>(null)

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0]
      if (activeTab && activeTab.url) {
        const url = new URL(activeTab.url)
        setIsOnCorrectPage(url.hostname === "app.vhsys.com.br")
      } else {
        setIsOnCorrectPage(false)
      }
    })
  }, [])

  if (!context) return <p>Context not available</p>
  const { data, error, hasConnectionIssue, firstLoad, ccDisplayAction } = context
  const shouldShowBlockedScreen =
    isOnCorrectPage === false || Boolean(error) || hasConnectionIssue

  useEffect(() => {
    window.dispatchEvent(
      new CustomEvent("rt:network-pause", {
        detail: { paused: shouldShowBlockedScreen }
      })
    )
  }, [shouldShowBlockedScreen])

  const handleReload = () => {
    window.location.reload()
  }

  if (firstLoad || isOnCorrectPage === null) return (      <Container>
        <ContainerHeader>
          <img src="https://raw.githubusercontent.com/ermsharo/RT_ASSETS/main/LOGO_TEST/E.png" />
          <h1>RT ENGENHARIA - VHSYS</h1>
        </ContainerHeader>
        <LoadingAnimation/>
      </Container>)

  if (shouldShowBlockedScreen) {
    return (
      <Container>
        <ContainerHeader>
          <img src="https://raw.githubusercontent.com/ermsharo/RT_ASSETS/main/LOGO_TEST/E.png" />
          <h1>RT ENGENHARIA - VHSYS</h1>
        </ContainerHeader>
        <p style={{ color: "red", padding: "1rem" }}>
          Esta extensão só funciona dentro so site{" "}
          <strong>app.vhsys.com.br</strong>.
        </p>
        <ReloadButton type="button" onClick={handleReload}>
          Recarregar
        </ReloadButton>
      </Container>
    )
  }

  return (
    <Container>
      <ContainerHeader>
        <img src="https://raw.githubusercontent.com/ermsharo/RT_ASSETS/main/LOGO_TEST/E.png" />
        <h1>RT ENGENHARIA - VHSYS</h1>
        <h3>V{updated_version}</h3>
        <ResetButton />
      </ContainerHeader>

      <ApiPopulateWorkflows />

      <AccordionItem
        serviceRef={ccDisplayAction}
        data={data}
        name="Relatorio de centro de custo "
        content={<RelatorioManagerCC />}
        progressBar ={<CCReportProgressBarTotal/>}
      />
      <AccordionItem
        serviceRef="REGULAR_BILLS"
        data={data}
        name="Despesas recorrentes"
        content={<RegularBills />}
        progressBar={<RegularBillsProgressBar />}
      />
      <AccordionItem
        serviceRef="EMPLOYERS"
        data={data}
        name="Dados de funcionario"
        content={<Employer />}
        progressBar={<EmployerProgressBar />}
      />
      <AccordionItem
        serviceRef="SERVICE_NF"
        data={data}
        name="Relatorio de notas serviço"
        content={<ServicesNoteReport />}
      />
      <AccordionItem
        serviceRef="SALES_NF"
        data={data}
        name="Relatorio de notas vendas "
        content={<SalesNF />}
      />
      <AccordionItem
        serviceRef="SERVICE_NF_MANAGER"
        data={data}
        name="NF de Serviço"
        content={<ServiceNF />}
        progressBar={<ServiceNFProgressBar />}
      />
    </Container>
  )
}
export default IndexPopup
