import React, { useState, useContext } from 'react';
import styled from "styled-components";
import ServiceStatus from '~components/ServiceStatus';
import { DataContext } from "../../context/DataContext";
import CCReportProgressBar from '~components/ProgressBar/CCReportProgressBar';

const CustomButton = styled.button`
    border: 1px solid transparent;
    line-height: 28px;
    font-family: Poppins;
    font-size: 14px;
    font-weight: 700;
    background-color: rgb(140, 4, 4);
    margin: 1rem;
    padding: 25px 50px;
    text-transform: uppercase;
    border-radius: 0px;
    color: white;
`;

const ServiceStatusInfoBox = styled.div`
  display: flex;
  flex-direction: column;
  border-radius: 1rem;
  transition: 0.9s;
  padding: 1rem;
  text-align: left;
`;

export default function RelatorioManagerCC() {
    const context = useContext(DataContext);
    if (!context)
        return <p>Context not available</p>;

    const { entries, outputs, total } = context;
    const [putLoading, setPutLoading] = useState<boolean>(false);

    const handlePutReset = async () => {
        setPutLoading(true);
        try {
            const response = await fetch('https://rt-extension-server.azurewebsites.net/cc_report/reset', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ entries, outputs, total }),
            });
            if (!response.ok) {
                throw new Error('Failed to execute PUT request');
            }
            const result = await response.json();
        } catch (error) {
            console.error("Error with PUT request:", error);
        } finally {
            setPutLoading(false);
        }
    };

    return (
        <ServiceStatusInfoBox>

            <ServiceStatus service="Relatorios de centro de custo" service_ref="CC_REPORT" >
                            <CCReportProgressBar />
            </ServiceStatus>

            <CustomButton onClick={handlePutReset} disabled={putLoading}>
                {putLoading ? "Atualizando..." : "Resetar processo"}
            </CustomButton>
        </ServiceStatusInfoBox>
    );
}
