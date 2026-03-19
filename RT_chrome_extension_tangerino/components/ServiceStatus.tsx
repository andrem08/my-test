import React, { useContext } from "react"
import styled from "styled-components"


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
 


  return (
    <ServiceStatusInfoBox>
      <h2>{service} </h2>
      <h4></h4>
      <div>{children}</div>

      {/* <CustomButton onClick={handleRunService}>Atualizar</CustomButton> */}
    </ServiceStatusInfoBox>
  )
}
export default ServiceStatus
