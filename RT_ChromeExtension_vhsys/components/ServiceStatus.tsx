import React, { useContext } from "react"
import styled from "styled-components"

import { DataContext } from "../context/DataContext"
import { cardStyles, primaryButtonStyles } from "./shared/styles"

const ServiceStatusInfoBox = styled.div`
  ${cardStyles};
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  transition: box-shadow 0.2s ease;
  padding: 1rem 1rem 1.15rem;
  text-align: left;

  h2 {
    margin: 0;
    font-size: 1.02rem;
    font-weight: 700;
    color: #312117;
    font-family: "Sora", "Manrope", sans-serif;
  }
`

const CustomButton = styled.button`
  ${primaryButtonStyles};
  align-self: flex-start;
  padding: 10px 14px;
`

function ServiceStatus({
  service,
  service_ref,
  children
}: {
  service: string
  service_ref: string
  children?: React.ReactNode
  progressBar?: React.ReactNode
}) {
  const context = useContext(DataContext)
  if (!context) return <p>Context not available</p>
  const { data, firstLoad, runService } = context
  const handleRunService = () => {
    runService(service_ref)
  }

  if (firstLoad) return <p>Loading...</p>

  const ItemsStatus = data.find(
    (serviceItem: { ACTION: string }) =>
      serviceItem.ACTION.trim() === service_ref.trim()
  )
  if (!ItemsStatus) {
    console.warn("No matching service found for:", service_ref)
    return <p>No matching service found</p>
  }
  return (
    <ServiceStatusInfoBox>
      <h2>{service}</h2>
      <div>{children}</div>
      <CustomButton onClick={handleRunService} aria-label={`Atualizar ${service}`}>
        Atualizar
      </CustomButton>
    </ServiceStatusInfoBox>
  )
}
export default ServiceStatus
