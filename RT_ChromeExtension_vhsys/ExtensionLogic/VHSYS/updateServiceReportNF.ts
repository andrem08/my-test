import { buildServerRoute } from '../env';
import { update_action_state } from '../actionStateManager';
function getCurrentDate(): string {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    return `${day}/${month}/${year}`;
}
export default class NFReportServiceProcessor {
    private nfReportUrl: string;
    private vhsysReportUrl: string;
    private currentDate: string;
    constructor() {
        this.nfReportUrl = buildServerRoute("service_nf_report");
        this.currentDate = getCurrentDate();
        this.vhsysReportUrl =
            `https://app.vhsys.com.br/Relatorio/Relatorio.Servico.JSON.php?Nome=&Cod=&Data1=&Data2=&Data3=&Data4=&Status=,Em%20Aberto,Em%20Andamento,Atendido,Cancelado&Vendedor=&NomeVendedor=&Valor1=&Valor2=&buscar=1`;
    }
    /* trunk-ignore(eslint/@typescript-eslint/no-explicit-any) */
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
    /* trunk-ignore(eslint/@typescript-eslint/no-explicit-any) */
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
            update_action_state("SERVICE_NF", 1);
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
            await update_action_state("SERVICE_NF", 2);
        }
    }
}
