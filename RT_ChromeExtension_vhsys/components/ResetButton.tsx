import React, { useState } from "react"
import styled from "styled-components"
import { buildServerRoute } from "~components/env"
import { primaryButtonStyles } from "./shared/styles"

const CustomButton = styled.button`
    ${primaryButtonStyles};
    margin: 0;
    min-width: 102px;
    padding: 8px 12px;
`

export default function RelatorioManagerCC() {
    const [putLoading, setPutLoading] = useState<boolean>(false)

    const handlePutReset = async () => {
        setPutLoading(true)

        try {
            const response = await fetch(buildServerRoute("clean_up"), {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                }
            })

            if (!response.ok) {
                throw new Error("Failed to execute PUT request")
            }

            await response.json()
        } catch (error) {
            console.error("Error with PUT request:", error)
        } finally {
            setPutLoading(false)
        }
    }

    return (
        <CustomButton
            onClick={handlePutReset}
            disabled={putLoading}
            aria-label="Limpar dados temporários"
            title="Limpar dados temporários">
            {putLoading ? "Limpando..." : "Limpar cache"}
        </CustomButton>
    )
}
