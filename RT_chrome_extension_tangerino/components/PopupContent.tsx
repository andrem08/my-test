import React, { useContext, useEffect, useState } from "react"
import { BiSolidDownArrow, BiSolidUpArrow } from "react-icons/bi"
import styled from "styled-components"
import LoadingAnimation from "~components/Loading"
import { updated_version } from "~/version"
import ResetButton from "~components/ResetButton"
import StatusIcon from "~components/StatusIcon"
import TangerinoUpdate from "./ServicesContent/TangerinoUpdate"

import CompletedProgressBar from "./ProgressBar/CompletedProgressBar"


const CommandGroupHeader = styled.div`
  padding: 0.9rem;
  display: flex;
  box-shadow: rgba(17, 12, 46, 0.15) 0px 48px 100px 0px;

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
  box-shadow: rgba(17, 12, 46, 0.15) 0px 48px 100px 0px;
  background-color: aliceblue;
  opacity: 0.5;

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
  border-radius: 1rem;
  transition: 0.9s;
  padding: 1rem;
`
const Container = styled.div`
  text-align: center;
  padding: 1rem 0;
  width: 600px;
`

const StatusBar = styled.div`

display: flex;
`
const ProgressBarAlign = styled.div`

padding-right: 0.5rem;
`
const ContainerHeader = styled.div`
  display: flex;
  flex-direction: column;
  padding-top: 2rem;
  text-align: center;
  padding-bottom: 2rem;

  h1 {
    font-size: 1.5rem;
  }
  img {
    width: 180px;
    margin: 0 auto;
  }
`
const ItemHeader = styled.div`
  display: flex;
  justify-content: space-between;
  width: 100%;
  padding: 0rem 1rem;
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
             <ProgressBarAlign>{isCompleted ? <CompletedProgressBar /> : progressBar}</ProgressBarAlign>

            <StatusIcon status={currentStatus} /></StatusBar>

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
  // const context = useContext(DataContext)
  const [isOnCorrectPage, setIsOnCorrectPage] = useState<boolean | null>(null)

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0]
      if (activeTab && activeTab.url) {
        const url = new URL(activeTab.url)
        // alert(`Current page url ${url.hostname}`)
        setIsOnCorrectPage(url.hostname === "app.tangerino.com.br")
      } else {
        setIsOnCorrectPage(false)
      }
    })
  }, [])

  if (isOnCorrectPage === null) return (<Container>
    <ContainerHeader>
      <img src="https://raw.githubusercontent.com/ermsharo/RT_ASSETS/main/LOGO_TEST/E.png" />
      <h1>RT ENGENHARIA - Tangerino</h1>
    </ContainerHeader>
    <LoadingAnimation />
  </Container>)

  if (!isOnCorrectPage) {
    return (
      <Container>
        <ContainerHeader>
          <img src="https://raw.githubusercontent.com/ermsharo/RT_ASSETS/main/LOGO_TEST/E.png" />
          <h1>RT ENGENHARIA - Tangerino</h1>
        </ContainerHeader>
        <p style={{ color: "red", padding: "1rem" }}>
          Esta extensão só funciona dentro so site 
          <strong> https://app.tangerino.com.br/ </strong>.
        </p>
      </Container>
    )
  }

  return (
    <Container>
      <ContainerHeader>
        <img src="https://raw.githubusercontent.com/ermsharo/RT_ASSETS/main/LOGO_TEST/E.png" />
        <h1>RT ENGENHARIA - Tangerino</h1>
        <h3>V{updated_version}</h3>
      <TangerinoUpdate/>
      </ContainerHeader>








    </Container>
  )
}
export default IndexPopup
