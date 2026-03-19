import { buildServerRoute } from '../env';
export function vhsys_log() {
    console.log('vhsys import working');
}
const executionManager = {
    "FREQUENT_BILLS": false,
    "EMPLOYERS": false,
    "EMPLOYERS_BENEFITS": false,
    "CC_REPORT": false,
};
async function fetchData(url: string): Promise<any> {
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
export async function runnerVHSYS() {
    try {
        console.log("Application started...");
        const update_status_here = await fetchData(buildServerRoute("get_update_extension_service_data"));
        console.log("Update status here", update_status_here);
    }
    catch (error) {
        console.error("Fatal error in start function:", error);
    }
}
