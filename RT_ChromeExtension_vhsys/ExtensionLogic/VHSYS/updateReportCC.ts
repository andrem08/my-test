import { update_action_state } from "../actionStateManager"
import { buildServerRoute } from "../env"

async function safeExecution<T>(
  fn: (...args: any[]) => Promise<T>,
  ...args: any[]
): Promise<T | null> {
  try {
    return await fn(...args)
  } catch (error) {
    console.error("Error in safeExecution:", error)
    update_action_state("CC_REPORT", -1)
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
async function updateNextUrl(url: string): Promise<void> {
  try {
    console.log("Processing next URL:", url)
    const data = await getData<any>(url)
    if (!data) {
      throw new Error(`Invalid data or missing URL: ${JSON.stringify(data)}`)
    }
    console.log("Data obj here ", data)
    const { url: dataUrl } = data
    console.log("Data without destruct", data)
    console.log("url here", dataUrl)
    console.log("Next URL extracted:", dataUrl)
    const dataReport: {
      data: any
    } | null = await getData(dataUrl.url)
    console.log("Data report:", dataReport)
    if (dataReport && Object.keys(dataReport).length > 0) {
      const ref = {
        data: dataReport.data,
        cc_id: data.url.cc_id,
        type: data.url.type
      }
      const postResponse = await postData(buildServerRoute("cc_report"), ref)
      console.log("Data posted successfully:", postResponse)
    } else {
      console.warn("dataReport is empty or null, skipping postData")
    }
  } catch (error) {
    console.error("Error in updateNextUrl:", error)
  }
}
async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
export async function updateReportCC(): Promise<void> {
  const statusUrl = buildServerRoute("cc_report_manage/status")
  const nextUrl = buildServerRoute("cc_report_manage/next_url")
  let running = true
  let success = true
  while (running) {
    try {
      const statusData = await safeExecution(getData, statusUrl)
      running =
        (
          statusData as {
            running: any
          }
        )?.running || false
      console.log("Loop running status:", running)
      if (running) {
        await safeExecution(updateNextUrl, nextUrl)
        await delay(10000)
      }
    } catch (error) {
      success = false
      break
    }
  }
  if (success) {
    console.log("Loop completed successfully, executing final logic...")
    await update_action_state("CC_REPORT", 2)
  } else {
    await update_action_state("CC_REPORT", -1)
  }
}
export async function updateReportCCMultiThread(
  instances: number
): Promise<void> {
  await update_action_state("CC_REPORT", 1)
  await Promise.all(Array.from({ length: instances }, () => updateReportCC()))
}
