const originalLog = console.log;
console.log = (...args) => {
    originalLog(...args);
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { type: 'log', args: args });
        }
    });
};


console.log("Background script from plasmo framework");