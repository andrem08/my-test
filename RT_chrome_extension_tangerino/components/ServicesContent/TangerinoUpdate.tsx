import React, { useState } from "react";
import styled from "styled-components";
import { SERVER_REF } from "~components/env";
import ServiceStatus from "~components/ServiceStatus";
const Container = styled.div `
  display: flex;
  flex-direction: column;
`;
const CustomButton = styled.button `
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
const updateOrRegisterEntry = async (token: string | null) => {
    if (!token) {
        console.error("No token found!");
        return;
    }
    try {
        //const response = await fetch(`${SERVER_REF}/tagerino/time_entry`, {
        const response = await fetch(`${SERVER_REF}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Accept: "*/*",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ tangerino_token: token }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
    }
    catch (error) {
        console.error("Error during fetch:", error);
    }
};
export default function TangerinoUpdate() {
    const [jwtToken, setJwtToken] = useState<string | null>(null);
    const fetchJwtToken = () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]?.id) {
                chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    func: () => {
                        const match = document.cookie
                            .split("; ")
                            .find((row) => row.startsWith("_user_session_jwt_token="));
                        return match ? match.split("=")[1] : null;
                    },
                }, (results) => {
                    if (chrome.runtime.lastError) {
                        console.error(chrome.runtime.lastError.message);
                        return;
                    }
                    const token = results?.[0]?.result || null;
                    console.log("Extracted token:", token);
                    setJwtToken(token);
                    updateOrRegisterEntry(token);
                });
            }
        });
    };
    return (<Container>
      <ServiceStatus service="Entradas tangerino" service_ref="TANGERINO"/>
      <CustomButton onClick={fetchJwtToken}>Get JWT Token</CustomButton>

    </Container>);
}
