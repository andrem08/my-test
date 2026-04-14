import { update_action_state } from "./actionStateManager";
import { AVALIABLE_SERVICES, buildServerRoute, type AvailableServices } from "./env";
import GetServiceNFInfo from "./VHSYS/getServiceNFInfo";
import GetServiceNFLabels from "./VHSYS/getServiceNFlabels";
import { updateEmployerInfo } from "./VHSYS/updateEmployersInfo";
import { updateFrequentBills } from "./VHSYS/updateFrequestBills";
import { updateReportCCMultiThread, updateReportCCLastSixMonthsMultiThread } from "./VHSYS/updateReportCC";
import NFReportSalesProcessor from "./VHSYS/updateSalesReportNF";
import NFReportServiceProcessor from "./VHSYS/updateServiceReportNF";

async function fetchData(url: string): Promise<unknown> {
    try {
        const response = await fetch(url, { method: "GET" });
        if (!response.ok) {
            throw new Error(`Failed to fetch data. Status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    }
    catch (error) {
        console.error("Error during fetch:", error);
        return null;
    }
}

type UpdateExtensionValue = {
    ACTION: string;
    LAST_RUN: string;
    LAST_UPDATE: string;
    PROGRESS_VALUE: number;
    RUN_AFTER: number;
    RUN_STATUS: number;
};

function isUpdateExtensionValueArray(data: unknown): data is UpdateExtensionValue[] {
    return Array.isArray(data);
}

function isAvailableServiceKey(value: string): value is keyof AvailableServices {
    return value in AVALIABLE_SERVICES;
}

export default class ServiceRunner {
    private service_data_url: string;
    private fetched_data: UpdateExtensionValue[] | null;
    private run_reference_data: AvailableServices;

    constructor() {
        this.service_data_url = buildServerRoute("get_update_extension_service_data");
        this.fetched_data = null;
        this.run_reference_data = { ...AVALIABLE_SERVICES };
        this.init();
    }

    private async init(): Promise<void> {
        await this.loadData();
    }

    private async loadData(): Promise<void> {
        const data = await fetchData(this.service_data_url);
        if (isUpdateExtensionValueArray(data)) {
            this.fetched_data = data;
        }
        else {
            console.error("Failed to load data.");
        }
    }

    public async refreshData(): Promise<void> {
        const data = await fetchData(this.service_data_url);
        if (isUpdateExtensionValueArray(data)) {
            this.fetched_data = data;

        }
    }

    public getData(): UpdateExtensionValue[] | null {
        return this.fetched_data;
    }

    public filterByServiceKey(dataArray: UpdateExtensionValue[], serviceKey: string): UpdateExtensionValue | undefined {
        return dataArray.find((item) => item.ACTION === serviceKey);
    }

    public async run_services(serviceKey: keyof AvailableServices): Promise<void> {
        console.log(` \n \n \n RUNNING SERVICE  ${serviceKey} \n \n \n`);
        try {
            if (serviceKey === "REGULAR_BILLS") {
                await updateFrequentBills();
            }
            else if (serviceKey === "CC_REPORT") {
                await updateReportCCMultiThread(5, "CC_REPORT");
            }
            else if (serviceKey === "CC_REPORT_3_MONTHS") {
                await updateReportCCLastSixMonthsMultiThread(5, "CC_REPORT_3_MONTHS");
            }
            else if (serviceKey === "EMPLOYERS") {
                update_action_state("EMPLOYERS", 1);
                await updateEmployerInfo("https://app.vhsys.com.br/index.php?Secao=Aplicativos&Modulo=Aplicativos&App=30");
                update_action_state("EMPLOYERS", 2);
            }
            else if (serviceKey === "SALES_NF") {
                const nfSalesReportProcessor = new NFReportSalesProcessor();
                await nfSalesReportProcessor.processNFReport();
            }
            else if (serviceKey === "SERVICE_NF") {
                const nfServiceReportProcessor = new NFReportServiceProcessor();
                await nfServiceReportProcessor.processNFReport();
            }
            else if (serviceKey === "SERVICE_NF_METADATA_MANAGER") {
                const nfServiceLabelsprocessor = new GetServiceNFLabels();
                await nfServiceLabelsprocessor.processNFlabes();
            }
            else if (serviceKey === "SERVICE_NF_MANAGER") {
                update_action_state("SERVICE_NF_MANAGER", 1);
                // update_action_state("SERVICE_NF_METADATA_MANAGER", 1);
                const nfServiceLabelsprocessor = new GetServiceNFLabels();
                // update_action_state("SERVICE_NF_METADATA_MANAGER", 2);
                await nfServiceLabelsprocessor.processNFlabes();
                const nfServiceInfoProcessor = new GetServiceNFInfo();
                await nfServiceInfoProcessor.processNFInfo();
                update_action_state("SERVICE_NF_MANAGER", 2);
            }
        }
        catch (error) {
            console.error(`Error running service ${serviceKey}:`, error);
        }
    }

    public find_by_run_status = (
        data: Array<Record<string, unknown>>,
        runStatus: number
    ) => {
        return (
            data.find(
                (obj) => Number(obj["RUN_STATUS"] ?? -999) === runStatus
            ) || false
        );
    };

    public isRunningService = (data) => {
        return this.find_by_run_status(data, 1);
    };

    public get_next_service = (data) => {
        return this.find_by_run_status(data, 0);
    };

    public verify_serice_and_run = (data: {
        ACTION: string;
        LAST_RUN: string;
        LAST_UPDATE: string;
        PROGRESS_VALUE: number;
        RUN_AFTER: number;
        RUN_STATUS: number;
    }[]) => {
        const isServiceRunning = this.isRunningService(data);
        console.log(isServiceRunning);
        if (isServiceRunning) {
            console.log("Service is running");
            return isServiceRunning["ACTION"];
        }
        else {
            const nextService = this.get_next_service(data);
            if (nextService) {
                console.log("Service is not running");
                console.log("Running next service");
                console.log(nextService["ACTION"]);
                return nextService["ACTION"];
            }
            else {
                console.log("No service to run");
                return false;
            }
        }
    };

    public delay(ms: number) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    public async resumeRunningServices(): Promise<void> {
        await this.refreshData();

        if (!this.fetched_data) {
            console.error("ServiceRunner: No data fetched for resume check.");
            return;
        }

        const runningServices = this.fetched_data
            .filter((service) => service.RUN_STATUS === 1)
            .map((service) => service.ACTION)
            .filter(isAvailableServiceKey);

        for (const serviceKey of runningServices) {
            console.log(`Service ${serviceKey} is marked running. Resuming execution.`);
            await this.run_services(serviceKey);
        }
    }
}
