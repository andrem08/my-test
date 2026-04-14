import { runnerVHSYS, vhsys_log } from "./ExtensionLogic/VHSYS/vhsys"

console.log("Runing content script from my-extension")
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "log") {
    console.log(...message.args)
  }
})
