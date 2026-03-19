import React, { useContext } from "react"
import styled from "styled-components"

import { DataContext } from "../context/DataContext"

const ServiceStatusInfoBox = styled.div`
  display: flex;
  flex-direction: column;
  border-radius: 1rem;
  transition: 0.9s;
  padding: 1rem;
  text-align: left;
`
const CustomButton = styled.button`
  border: 1px solid transparent;

  font-family: Poppins;
  font-size: 14px;
  font-weight: 700;
  background-color: rgb(140, 4, 4);

  padding: 4px 4px;
  text-transform: uppercase;
  border-radius: 0px;
  color: white;
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
      <h2>{service} </h2>
      <h4></h4>
      <div>{children}</div>

      <CustomButton onClick={handleRunService}>Atualizar</CustomButton>
    </ServiceStatusInfoBox>
  )
}
export default ServiceStatus
