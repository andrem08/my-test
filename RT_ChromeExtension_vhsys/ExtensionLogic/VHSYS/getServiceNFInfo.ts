import { update_action_state } from "../actionStateManager"
import { buildServerRoute } from "../env"

export default class GetServiceNFInfo {
  private nfIdsUrl: string
  private nfInfoUrl: string
  private vhsysReportUrl: string
  constructor() {
    this.nfIdsUrl = buildServerRoute("nf_service_labels_ids")
    this.nfInfoUrl = buildServerRoute("nf_service_info")
    this.vhsysReportUrl = `https://app.vhsys.com.br/index.php?Secao=Servicos.Emitir&Modulo=Servicos`
  }
  private drawProgressBar(current: number, total: number): void {
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
  private async fetchPageData(page_id: string): Promise<string | null> {
    const url =
      "https://app.vhsys.com.br/index.php?Secao=Servicos.Emitir&Modulo=Servicos"
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
          Accept: "*/*",
          Referer: `https://app.vhsys.com.br/index.php?Secao=Servicos.Emitir&Modulo=Servicos`
        },
        body: `xajax=ObterDados&xajaxr=1739443376675&xajaxargs[]=${page_id}&xajaxargs[]=`
      })
      if (!response.ok) {
        throw new Error(`Failed to fetch data. Status: ${response.status}`)
      }
      const responseText = await response.arrayBuffer()
      const decoder = new TextDecoder("ISO-8859-1")
      const decodedText = decoder.decode(responseText)
      const postResponse = await fetch(this.nfInfoUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ xml_ref: decodedText })
      })
      if (!postResponse.ok) {
        throw new Error(
          `HTTP error during POST! Status: ${postResponse.status}`
        )
      }
      return decodedText
    } catch (error) {
      console.error(`\nError fetching data for page_id ${page_id}:`, error)
      return null
    }
  }
  private async fetchData(url: string): Promise<any> {
    try {
      const response = await fetch(url, {
        method: "GET"
      })
      if (!response.ok) {
        throw new Error(`Failed to fetch data. Status: ${response.status}`)
      }
      const data = await response.json()
      return data
    } catch (error) {
      console.error("Error during fetch:", error)
      return null
    }
  }
  private async getNFPage(page_id: string) {
    try {
      await this.fetchPageData(page_id)
    } catch (error) {}
  }
  public async processNFInfo(): Promise<void> {
    try {
      const get_url_ids = await this.fetchData(this.nfIdsUrl)
      if (!get_url_ids || !get_url_ids.data || get_url_ids.data.length === 0) {
        console.log("No items to process.")
        return
      }
      const items = get_url_ids.data
      const totalItems = items.length
      const batchSize = 5

      // Get the last processed index from storage
      const result = await new Promise<{
        serviceNFInfoProgress?: { progress: number, total: number }
      }>((resolve) =>
        chrome.storage.local.get("serviceNFInfoProgress", (result) =>
          resolve(result as { serviceNFInfoProgress?: { progress: number, total: number } })
        )
      )
      const startIndex = result.serviceNFInfoProgress?.progress || 0

      let processedCount = startIndex
      console.log(
        `Starting to process ${totalItems} items in batches of ${batchSize}...`
      )
      if (startIndex > 0) {
        console.log(`Resuming from index ${startIndex}.`)
      }
      this.drawProgressBar(processedCount, totalItems)

      for (let i = startIndex; i < totalItems; i += batchSize) {
        const batch = items.slice(i, i + batchSize)
        const batchPromises = batch.map((item) => {
          const nf_id = item.codigo
          return this.getNFPage(nf_id)
        })
        await Promise.all(batchPromises)
        processedCount += batch.length
        this.drawProgressBar(processedCount, totalItems)

        // Save the next index to process
        await new Promise<void>((resolve) =>
          chrome.storage.local.set(
            { serviceNFInfoProgress: { progress: i + batchSize, total: totalItems, label: "serviceNFInfoProgress" } },
            resolve
          )
        )
      }

      await new Promise<void>((resolve) =>
        chrome.storage.local.remove("serviceNFInfoProgress", resolve)
      )
      console.log("Processing complete. Saved index cleared.")
    } catch (error) {
      console.error("An error occurred during the process:", error)
    }
  }
}
