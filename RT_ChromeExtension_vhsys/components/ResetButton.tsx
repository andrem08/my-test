import React, { useEffect, useMemo, useState } from "react";
import styled from "styled-components";
import { buildServerRoute } from "~components/env";
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
export default function RelatorioManagerCC() {
    const [putLoading, setPutLoading] = useState<boolean>(false);
    const handlePutReset = async () => {
        setPutLoading(true);
        try {
            const response = await fetch(buildServerRoute("clean_up"), {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                }
            });
            if (!response.ok) {
                throw new Error("Failed to execute PUT request");
            }
            const result = await response.json();
        }
        catch (error) {
            console.error("Error with PUT request:", error);
        }
        finally {
            setPutLoading(false);
        }
    };
    return (<CustomButton onClick={handlePutReset} disabled={putLoading}>
      {putLoading ? "⟲" : "⟳"}
    </CustomButton>);
}
