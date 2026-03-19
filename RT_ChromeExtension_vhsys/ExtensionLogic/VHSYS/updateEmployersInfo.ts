import { update_action_state } from "../actionStateManager"
import { buildServerRoute } from "../env"

async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
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

async function fetchAndPostData(getUrl: string, postUrl: string) {
  try {
    const getResponse = await fetch(getUrl)
    if (!getResponse.ok) {
      throw new Error(`HTTP error during GET! Status: ${getResponse.status}`)
    }
    const data = await getResponse.json()

    const postResponse = await fetch(postUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })

    if (!postResponse.ok) {
      throw new Error(`HTTP error during POST! Status: ${postResponse.status}`)
    }
    const postResult = await postResponse.json()
    return postResult
  } catch (error) {
    console.error("Error in fetch or post process:", error)
    return null
  }
}

export async function updateEmployerInfo(url: string, user_id = null) {
  let success = true


  await fetchAndPostData(
    "https://app.vhsys.com.br/Aplicativos/Funcionarios/Relatorio.Funcionarios.JSON.php?Nome=&Matricula=&Cargo=&Status=&buscar=1",
    buildServerRoute(
      "employers_general_data?rt_token=YfdDQlECBBBXTwAqsrCLU88jds465VbPIevKuZnKLP9N4OwFl"
    )
  )
    .then((postResult) => console.log("Post result:", postResult))
    .catch((error) => {
      console.error(error)
      success = false // Note: this success flag might not behave as expected due to async nature.
    })

  // Helper function to post data using XMLHttpRequest.
  const postData = (url: string, data: any) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open("POST", url, true)
      xhr.setRequestHeader("Content-Type", "application/json")
      xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const responseData = JSON.parse(xhr.responseText)
            resolve(responseData)
          } catch (e) {
            console.error("Failed to parse JSON response:", e)
            reject(e)
            success = false
          }
        } else {
          console.error("Request failed with status:", xhr.status)
          reject(new Error(`Request failed with status ${xhr.status}`))
        }
      }
      xhr.onerror = function () {
        console.error("Request failed")
        reject(new Error("Network error"))
      }
      xhr.send(JSON.stringify(data))
    })
  }

  // Fetches detailed data for a single user.
  const fetchDataUser = async (user_id: string) => {
    try {
      const response = await fetch(
        "https://app.vhsys.com.br/index.php?Secao=Aplicativos&Modulo=Aplicativos&App=30",
        {
          headers: {
            accept: "*/*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "sec-ch-ua":
              '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "sec-ch-ua-platform": '"Windows"'
          },
          method: "POST",
          body: `xajax=ObterDados&xajaxr=1726157531287&xajaxargs[]=${user_id}`
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const responseText = await response.arrayBuffer()
      const decoder = new TextDecoder("ISO-8859-1")
      const decodedText = decoder.decode(responseText)

      const employers_plus_url = buildServerRoute(
        "employers_plus_info?rt_token=YfdDQlECBBBXTwAqsrCLU88jds465VbPIevKuZnKLP9N4OwFl"
      )
      const data_post = { xml_ref: decodedText }

      // Adding a delay before posting the data.
      await postData(employers_plus_url, data_post)
    } catch (error) {
      console.error(`Error during fetch for user ${user_id}:`, error)
      success = false
    }
  }

  try {
    const response = await fetch(url, {
      headers: {
        accept: "*/*",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "sec-ch-ua": '"Chromium";v="128", "Google Chrome";v="128"'
      },
      method: "POST",
      body: user_id ? `xajax=ObterDados&xajaxargs[]=${user_id}` : "xajax=Listar"
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.text()
    console.log("Fetch successful!", data)

    const employers_plus_url = buildServerRoute(
      "employers_plus?rt_token=YfdDQlECBBBXTwAqsrCLU88jds465VbPIevKuZnKLP9N4OwFl"
    )
    const data_post = { xml_ref: data }
    /* trunk-ignore(eslint/@typescript-eslint/no-explicit-any) */
    const postResponse: any = await postData(employers_plus_url, data_post)

    await delay(500) // Ensures the delay completes before proceeding.

    console.log("Post data response:", postResponse)

    if (postResponse && postResponse.ids) {
      const items = postResponse.ids
      const totalItems = items.length
      let processedCount = 0

      console.log(`Starting to process ${totalItems} items...`)
      drawProgressBar(processedCount, totalItems)

      for (const item of items) {
        console.log(`Buscando dados para o usuário código: ${item.codigo}...`)
        await fetchDataUser(item.codigo)
        processedCount++
        drawProgressBar(processedCount, totalItems)
        chrome.storage.local.set({
          employerUpdateProgress: {
            progress: processedCount,
            total: totalItems,
            label: "Employer Update"
          }
        })
        console.log(`...Dados para o usuário ${item.codigo} foram processados.`)
      }
    }
  } catch (error) {
    console.error("Error during main fetch process:", error)
    success = false
  }

  if (success) {
    console.log("Todos os funcionários foram atualizados com sucesso!")
    chrome.storage.local.remove("employerUpdateProgress")
  } else {
    console.log("Ocorreram erros durante a atualização dos funcionários.")
  }
}
