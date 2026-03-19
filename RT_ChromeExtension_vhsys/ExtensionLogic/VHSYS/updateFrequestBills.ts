import { update_action_state } from "../actionStateManager"
import { buildServerRoute } from "../env"

async function getDataWithToken<T>(
  url: string,
  token: string
): Promise<T | null> {
  try {
    const response = await fetch(url, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`
      }
    })
    if (!response.ok) {
      throw new Error(`Failed to fetch data with token: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error("Error in getDataWithToken:", { url, error })
    return null
  }
}
async function postData<T>(url: string, bodyData: unknown): Promise<T | null> {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(bodyData)
    })
    if (!response.ok) {
      throw new Error(
        `Failed to post data to ${url}, status: ${response.status}`
      )
    }
    return await response.json()
  } catch (error) {
    console.error("Error in postData:", { url, error })
    return null
  }
}
async function getCookie(name: string, url: string): Promise<string | null> {
  if (!url) {
    console.error("URL is required to get a cookie.")
    return null
  }
  try {
    const cookie = await chrome.cookies.get({ url, name })
    if (cookie) {
      console.log(`Cookie "${name}" found for URL: ${url}`)
      return cookie.value
    } else {
      console.log(
        `Cookie "${name}" not found for URL: ${url}. Trying base domain.`
      )
      const urlObj = new URL(url)
      const domainParts = urlObj.hostname.split(".")
      if (domainParts.length > 2) {
        const baseDomain = domainParts.slice(-2).join(".")
        const fallbackUrl = `${urlObj.protocol}//${baseDomain}`
        const fallbackCookie = await chrome.cookies.get({
          url: fallbackUrl,
          name
        })
        if (fallbackCookie) {
          console.log(`Cookie "${name}" found for fallback URL: ${fallbackUrl}`)
          return fallbackCookie.value
        }
      }
      console.log(
        `Cookie "${name}" not found for URL: ${url} or its base domain.`
      )
      return null
    }
  } catch (e) {
    console.error(
      `Could not get cookie "${name}". Make sure you have "cookies" and host permissions for ${url} in your manifest.`,
      e
    )
    return null
  }
}
async function getActiveTabUrl(): Promise<string | null> {
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true })
    if (tabs.length > 0 && tabs[0].url) {
      return tabs[0].url
    }
    console.error(
      "Could not get active tab URL. Make sure there is an active tab."
    )
    return null
  } catch (e) {
    console.error("Error querying tabs:", e)
    return null
  }
}
function drawProgressBar(current: number, total: number): void {
  const barLength = 40
  const percentage = Math.floor((current / total) * 100)
  const filledLength = Math.round(barLength * (current / total))
  const emptyLength = barLength - filledLength
  const filledBar = "█".repeat(filledLength)
  const emptyBar = "─".repeat(emptyLength)
  console.log(
    `Processing: [${filledBar}${emptyBar}] ${percentage}% (${current}/${total})`
  )
}
export async function updateFrequentBills(): Promise<void> {
  console.log("Updating frequent bills...")
  try {
    update_action_state("REGULAR_BILLS", 1)
    const activeTabUrl = await getActiveTabUrl()
    if (!activeTabUrl) {
      throw new Error("Could not get active tab URL to retrieve cookie.")
    }
    const token = await getCookie("token", activeTabUrl)
    if (!token) {
      throw new Error(
        "Missing 'token' cookie. Ensure you are logged in to vhsys on the active tab."
      )
    }
    console.log("Token found, proceeding with API call.")
    let currentPage = 1
    const limit = 100
    let maxPage = 1
    const allBills: any[] = []
    const initialUrl = `https://api.app.vhsys.com.br/v1/financeiro/despesas/recorrentes/?limite=${limit}&pagina=1`
    const initialResponse = await getDataWithToken<any>(initialUrl, token)
    if (
      initialResponse &&
      initialResponse.dados &&
      initialResponse.dados.paginacao
    ) {
      maxPage = initialResponse.dados.paginacao.ultima_pagina
      console.log(`Total pages to fetch: ${maxPage}`)
      if (initialResponse.dados.dados) {
        allBills.push(...initialResponse.dados.dados)
      }
      drawProgressBar(1, maxPage)
    } else {
      console.error(
        "Failed to fetch initial page or get pagination data. Response:",
        initialResponse
      )
      update_action_state("REGULAR_BILLS", -1)
      return
    }
    if (maxPage > 1) {
      for (let page = 2; page <= maxPage; page++) {
        const url = `https://api.app.vhsys.com.br/v1/financeiro/despesas/recorrentes/?limite=${limit}&pagina=${page}`
        const response = await getDataWithToken<any>(url, token)
        if (response && response.dados && response.dados.dados) {
          allBills.push(...response.dados.dados)
        } else {
          console.error(`Failed to fetch data for page ${page}.`)
        }
        drawProgressBar(page, maxPage)
        chrome.storage.local.set({
          frequentBillsProgress: {
            progress: page,
            total: maxPage,
            label: "Frequent Bills Update"
          }
        })
      }
    }
    console.log("\nAll frequent bills fetched successfully.")
    const postResponse = await postData(buildServerRoute("regular_bills"), allBills)
    console.log("Frequent bills updated on server:", postResponse)
    update_action_state("REGULAR_BILLS", 2)
    chrome.storage.local.remove("frequentBillsProgress")
  } catch (error) {
    console.error("Error in updateFrequentBills:", error)
    update_action_state("REGULAR_BILLS", -1)
    chrome.storage.local.remove("frequentBillsProgress")
  }
}
