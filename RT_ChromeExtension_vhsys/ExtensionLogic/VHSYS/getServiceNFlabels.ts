import { buildServerRoute } from "../env"

function getCurrentDate(): string {
  const now = new Date()
  const day = String(now.getDate()).padStart(2, "0")
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const year = now.getFullYear()
  return `${day}/${month}/${year}`
}
export default class GetServiceNFLabels {
  private nfReportUrl: string
  private vhsysReportUrl: string
  private currentDate: string
  constructor() {
    this.nfReportUrl = buildServerRoute("nf_service_labels")
    this.currentDate = getCurrentDate()
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
      `Processing Pages: [${filledBar}${emptyBar}] ${percentage}% (${current}/${total})`
    )
  }
  private getCookieValue(cookieName: string): string | null {
    const cookies = document.cookie.split(";")
    for (let cookie of cookies) {
      cookie = cookie.trim()
      if (cookie.startsWith(`${cookieName}=`)) {
        return cookie.substring(cookieName.length + 1)
      }
    }
    return null
  }
  private async fetchData(page: number): Promise<string | null> {
    const url = `${this.vhsysReportUrl}#!pagina/${page}`
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
          Accept: "*/*",
          Referer: `https://app.vhsys.com.br/index.php?Secao=Servicos.Emitir&Modulo=Servicos#!pagina/${page}`
        },
        body: `xajax=Listar&xajaxr=[]&xajaxargs[]=&xajaxargs[]=${page}&xajaxargs[]=0&xajaxargs[]=showNomeFantasiaFalse&xajaxargs[]=0`
      })
      if (!response.ok) {
        throw new Error(`Failed to fetch data. Status: ${response.status}`)
      }
      const data = await response.text()
      return data
    } catch (error) {
      console.error(`Error fetching data for page ${page}:`, error)
      return null
    }
  }
  private async postData(data: any): Promise<any> {
    try {
      const response = await fetch(this.nfReportUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      })
      if (!response.ok) {
        throw new Error(`Failed to post data. Status: ${response.status}`)
      }
      const result = await response.json()
      return result
    } catch (error) {
      console.error("Error during POST:", error)
      return null
    }
  }
  public async processNFlabes(): Promise<void> {
    const totalPages = 1
    console.log(`Starting Service NF Report process for ${totalPages} pages...`)
    try {
      for (let i = 1; i <= totalPages; i++) {
        chrome.storage.local.set({
          serviceNFLabelsProgress: {
            progress: i,
            total: totalPages,
            label: "serviceNFLabelsProgress"
          }
        })
        this.drawProgressBar(i - 1, totalPages)
        const fetchedData = await this.fetchData(i)
        if (!fetchedData) {
          console.error(
            `Failed to fetch data for page ${i}. Skipping this page.`
          )
          continue
        }
        const decoder = new TextDecoder("ISO-8859-1")
        const decodedText = decoder.decode(
          new TextEncoder().encode(fetchedData)
        )
        const postResult = await this.postData(decodedText)
        if (!postResult) {
          console.error(
            `Failed to post data for page ${i}. Skipping this page.`
          )
        }
        await new Promise((resolve) => setTimeout(resolve, 1000))
      }
     chrome.storage.local.remove("serviceNFLabelsProgress")
      this.drawProgressBar(totalPages, totalPages)
      console.log("Processing complete!")
    } catch (error) {
      chrome.storage.local.remove("serviceNFLabelsProgress")
      console.error("An unexpected error occurred during the process:", error)
    }
  }
}
