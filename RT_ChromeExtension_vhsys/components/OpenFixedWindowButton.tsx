import React from "react"
import styled from "styled-components"

import { primaryButtonStyles } from "./shared/styles"

const FixedWindowButton = styled.button`
  ${primaryButtonStyles};
  background: linear-gradient(130deg, #5f4b3a 0%, #3f2f22 100%);
  border-color: rgba(63, 47, 34, 0.28);
  min-width: 116px;
`

export default function OpenFixedWindowButton() {
  const handleOpenFixedWindow = () => {
    const popupUrl = chrome.runtime.getURL("popup.html")

    chrome.windows.create({
      url: popupUrl,
      type: "popup",
      width: 460,
      height: 760,
      focused: true
    })
  }

  return (
    <FixedWindowButton
      onClick={handleOpenFixedWindow}
      title="Abrir em janela fixa"
      aria-label="Abrir extensão em janela fixa">
      Abrir fixo
    </FixedWindowButton>
  )
}
