import React from "react"

import "./index.css"

import IndexPopup from "~components/PopupContent"

// import { DataProvider } from "./context/DataContext"

const originalLog = console.log
console.log = (...args) => {
  originalLog(...args)
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { type: "log", args: args })
    }
  })
}

function Popup() {
  return (

      <IndexPopup />

  )
}
export default Popup
