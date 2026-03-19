import { buildServerRoute } from '../env';
import { update_action_state } from '../actionStateManager';
function getCurrentDate(): string {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    return `${day}/${month}/${year}`;
}
export default class NFReportSalesProcessor {
    private nfReportUrl: string;
    private vhsysReportUrl: string;
    private currentDate: string;
    constructor() {
        this.nfReportUrl = buildServerRoute("sales_nf_report");
        this.currentDate = getCurrentDate();
        this.vhsysReportUrl =
            `https://app.vhsys.com.br/Relatorio/Relatorio.Vendas.JSON.php?Nome=&Cod=&Data1=&Data2=&Data3=01/07/2000&Data4=${this.currentDate}&Status=,Em%20Aberto,Em%20Andamento,Atendido,Cancelado&Tipo=&Finalidade=&Vendedor=&NomeVendedor=&CFOP=&Valor1=&Valor2=&ExibirProd=&ExibirMed=&Data5=&Data6=&Data7=&Data8=&Lote=&DataCadPedidoInicio=&DataCadPedidoFim=&DataEmissaoInicio=&DataEmissaoFim=&empresas_multi=null&buscar=1`;
        console.log(`Or url here from sales nf report ${this.vhsysReportUrl}`);
    }
    private async fetchData(url: string): Promise<any> {
        console.log(`Fetching data from: ${url}`);
        try {
            const response = await fetch(url, {
                method: "GET",
            });
            if (!response.ok) {
                throw new Error(`Failed to fetch data. Status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Fetched data:", data);
            return data;
        }
        catch (error) {
            console.error("Error during fetch:", error);
            return null;
        }
    }
    private async postData(url: string, data: any): Promise<any> {
        console.log(`Posting data to: ${url}`);
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                throw new Error(`Failed to post data. Status: ${response.status}`);
            }
            const result = await response.json();
            console.log("Server response:", result);
            return result;
        }
        catch (error) {
            console.error("Error during POST:", error);
            return null;
        }
    }
    public async processNFReport(): Promise<void> {
        let success = true;
        try {
            console.log("Starting NF Report process...");
            update_action_state("SALES_NF", 1);
            const fetchedData = await this.fetchData(this.vhsysReportUrl);
            const fetchDefaultData = await this.fetchData(buildServerRoute("health"));
            console.log("Default data", fetchDefaultData);
            if (!fetchedData) {
                console.error("Failed to fetch data. Exiting process.");
                success = false;
            }
            const postResult = await this.postData(this.nfReportUrl, fetchedData);
            if (!postResult) {
                console.error("Failed to post data. Exiting process.");
                success = false;
            }
            console.log("Process completed successfully!");
        }
        catch (error) {
            success = false;
            console.error("Unexpected error during process:", error);
            success = false;
        }
        if (success) {
            console.log("Loop completed successfully, executing final logic...");
            await update_action_state('SALES_NF', 2);
        }
    }
}
