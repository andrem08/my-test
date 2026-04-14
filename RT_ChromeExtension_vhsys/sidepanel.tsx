import React, { useEffect } from "react"

import "./index.css"

import IndexPopup from "~components/PopupContent"

import { DataProvider } from "./context/DataContext"

const originalLog = console.log
console.log = (...args) => {
  originalLog(...args)
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { type: "log", args })
    }
  })
}

function SidePanel() {
  useEffect(() => {
    const isConnectionIssue = (message: string) => {
      const normalized = message.toLowerCase()
      return (
        normalized.includes("could not establish connection") ||
        normalized.includes("receiving end does not exist") ||
        normalized.includes("unexpected end of json input")
      )
    }

    const notifyIssue = (payload: unknown) => {
      window.dispatchEvent(
        new CustomEvent("rt:connection-issue", {
          detail: { source: "sidepanel-runtime", payload }
        })
      )
    }

    const onUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason
      const message = reason instanceof Error ? reason.message : String(reason ?? "")
      if (isConnectionIssue(message)) {
        notifyIssue(reason)
      }
    }

    const onError = (event: ErrorEvent) => {
      const message = event.message || ""
      if (isConnectionIssue(message)) {
        notifyIssue({ message })
      }
    }

    window.addEventListener("unhandledrejection", onUnhandledRejection)
    window.addEventListener("error", onError)

    return () => {
      window.removeEventListener("unhandledrejection", onUnhandledRejection)
      window.removeEventListener("error", onError)
    }
  }, [])

  return (
    <DataProvider>
      <IndexPopup />
    </DataProvider>
  )
}

export default SidePanel
