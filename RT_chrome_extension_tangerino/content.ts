import ServiceRunner from "./ExtensionLogic/updateManager"
import { runnerVHSYS, vhsys_log } from "./ExtensionLogic/VHSYS/vhsys"

console.log("Runing content script from my-extension")
const servRunner = new ServiceRunner()
servRunner.run_data()
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "log") {
    console.log(...message.args)
  }
})
