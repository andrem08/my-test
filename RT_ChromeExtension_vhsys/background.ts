const originalLog = console.log

console.log = (...args) => {
    originalLog(...args)
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { type: "log", args })
        }
    })
}

const configureSidePanel = async () => {
    if (!chrome.sidePanel) return

    await chrome.sidePanel.setOptions({
        path: "sidepanel.html",
        enabled: true
    })

    await chrome.sidePanel.setPanelBehavior({
        openPanelOnActionClick: true
    })
}

void configureSidePanel().catch((error) => {
    console.error("Failed to configure side panel behavior:", error)
})

chrome.runtime.onInstalled.addListener(() => {
    void configureSidePanel().catch((error) => {
        console.error("Failed to configure side panel behavior on install:", error)
    })
})

chrome.runtime.onStartup.addListener(() => {
    void configureSidePanel().catch((error) => {
        console.error("Failed to configure side panel behavior on startup:", error)
    })
})

console.log("Background script from plasmo framework")