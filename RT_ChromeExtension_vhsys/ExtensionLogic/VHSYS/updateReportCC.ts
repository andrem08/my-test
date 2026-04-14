import { update_action_state } from "../actionStateManager"
import { buildServerRoute } from "../env"

export type CCActionKey = "CC_REPORT" | "CC_REPORT_3_MONTHS"

function signalConnectionIssue(source: string, detail?: unknown): void {
  if (typeof window === "undefined") return

  window.dispatchEvent(
    new CustomEvent("rt:connection-issue", {
      detail: { source, detail }
    })
  )
}

async function safeExecution<T>(
  fn: (...args: unknown[]) => Promise<T>,
  ...args: unknown[]
): Promise<T | null> {
  try {
    return await fn(...args)
  } catch (error) {
    console.error("Error in safeExecution:", error)
    return null
  }
}
async function getData<T>(url: string): Promise<T | null> {
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(
        `Failed to fetch data from ${url}, status: ${response.status}`
      )
    }
    const data: T = await response.json()
    console.log("Fetched data:", data)
    if (!data || Object.keys(data).length === 0) {
      console.warn(`Warning: Empty or invalid response from ${url}`)
      return null
    }
    return data
  } catch (error) {
    signalConnectionIssue("getData", { url, error })
    console.error("Error in getData:", { url, error })
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

type NextUrlResponse = {
  url: {
    url: string
    cc_id: string
    type: string
  }
}

async function updateNextUrl(url: string): Promise<void> {
  try {
    console.log("Processing next URL:", url)
    const data = await getData<NextUrlResponse>(url)
    if (!data) {
      throw new Error(`Invalid data or missing URL: ${JSON.stringify(data)}`)
    }
    console.log("Data obj here ", data)
    const { url: dataUrl } = data
    console.log("Data without destruct", data)
    console.log("url here", dataUrl)
    console.log("Next URL extracted:", dataUrl)
    const dataReport: { data?: unknown } | null = await getData(dataUrl.url)
    console.log("Data report:", dataReport)
    if (dataReport && Object.keys(dataReport).length > 0) {
      const ref = {
        data: dataReport.data,
        cc_id: dataUrl.cc_id,
        type: dataUrl.type
      }
      const postResponse = await postData(buildServerRoute("cc_report"), ref)
      console.log("Data posted successfully:", postResponse)
    } else {
      signalConnectionIssue("updateNextUrl-empty-report", { url: dataUrl?.url })
      console.warn("dataReport is empty or null, skipping postData")
    }
  } catch (error) {
    signalConnectionIssue("updateNextUrl", { url, error })
    console.error("Error in updateNextUrl:", error)
  }
}
async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function buildRouteWithQuery(
  route: string,
  query: Record<string, string | number | boolean | undefined>
): string {
  const url = new URL(buildServerRoute(route))

  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined) return
    url.searchParams.set(key, String(value))
  })

  return url.toString()
}

async function runUpdateReportCCLoop(
  statusUrl: string,
  nextUrl: string
): Promise<boolean> {
  let running = true
  let success = true
  while (running) {
    try {
      const statusData = await safeExecution(getData, statusUrl)
      if (!statusData) {
        success = false
        break
      }
      running =
        (
          statusData as {
            running: boolean
          }
        )?.running || false
      console.log("Loop running status:", running)
      if (running) {
        const updateResult = await safeExecution(updateNextUrl, nextUrl)
        if (updateResult === null) {
          success = false
          break
        }
        await delay(10000)
      }
    } catch {
      success = false
      break
    }
  }

  return success
}

export async function updateReportCC(): Promise<boolean> {
  const statusUrl = buildServerRoute("cc_report_manage/status")
  const nextUrl = buildServerRoute("cc_report_manage/next_url")
  return await runUpdateReportCCLoop(statusUrl, nextUrl)
}

export async function updateReportCCLastSixMonths(): Promise<boolean> {
  const statusUrl = buildRouteWithQuery("cc_report_manage/status", {
    months_back: 3
  })
  const nextUrl = buildRouteWithQuery("cc_report_manage/next_url", {
    months_back: 3
  })
  return await runUpdateReportCCLoop(statusUrl, nextUrl)
}

export async function updateReportCCMultiThread(
  instances: number,
  actionKey: CCActionKey = "CC_REPORT"
): Promise<void> {
  await update_action_state(actionKey, 1)
  const results = await Promise.all(Array.from({ length: instances }, () => updateReportCC()))
  const allSucceeded = results.every(Boolean)
  await update_action_state(actionKey, allSucceeded ? 2 : -1)
}

export async function updateReportCCLastSixMonthsMultiThread(
  instances: number,
  actionKey: CCActionKey = "CC_REPORT_3_MONTHS"
): Promise<void> {
  await update_action_state(actionKey, 1)
  const results = await Promise.all(
    Array.from({ length: instances }, () => updateReportCCLastSixMonths())
  )
  const allSucceeded = results.every(Boolean)
  await update_action_state(actionKey, allSucceeded ? 2 : -1)
}
