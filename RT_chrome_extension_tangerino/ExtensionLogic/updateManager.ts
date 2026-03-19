import { update_action_state } from "./actionStateManager";
import { AVALIABLE_SERVICES, SERVER_REF, type AvailableServices } from "../components/env";


async function fetchData(url: string): Promise<any> {
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

export default class ServiceRunner {
    private service_data_url: string;
    private fetched_data: UpdateExtensionValue[] | null;
    private run_reference_data: AvailableServices;

    constructor(baseUrl: string = SERVER_REF) {
        this.service_data_url = `${baseUrl}/get_update_extension_service_data`;
        this.fetched_data = null;
        this.run_reference_data = { ...AVALIABLE_SERVICES };
        this.init().then(() => {
            this.run_data();
        });
    }

    private async init(): Promise<void> {
        await this.loadData();
    }

    private async loadData(): Promise<void> {
        const data = await fetchData(this.service_data_url);
        if (data) {
            this.fetched_data = data;
        }
        else {
            console.error("Failed to load data.");
        }
    }

    public async refreshData(): Promise<void> {
        const data = await fetchData(this.service_data_url);
        if (data) {
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
        
    }
    public find_by_run_status = (data, runStatus) => {
        return (data.find((obj: {
            [x: string]: any;
        }) => obj["RUN_STATUS"] === runStatus) || false);
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

    public async run_data(): Promise<void> {
        await this.refreshData(); 

        if (!this.fetched_data) {
            console.error("ServiceRunner: No data fetched for initial check.");
            return;
        }

        for (const service of this.fetched_data) {
            if (service.RUN_STATUS === 1) {
                console.log(`Service ${service.ACTION} is running. Attempting to re-run.`);
                await this.run_services(service.ACTION as keyof AvailableServices);
            }
        }
    }
}
