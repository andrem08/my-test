const DEV_MODE = true;

export const SERVER_REF = DEV_MODE
    ? "https://n8n.srv1252717.hstgr.cloud/webhook/8e1d053b-4df1-4cdd-b532-bc6b596a14ed"
    : "https://rt-extension-server-hmbedya2dfh0arg2.canadacentral-01.azurewebsites.net";

export function buildServerRoute(route: string): string {
    const normalizedRoute = route.replace(/^\/+/, "");

    if (DEV_MODE) {
        const webhookUrl = new URL(SERVER_REF);
        webhookUrl.searchParams.set("route", normalizedRoute);
        return webhookUrl.toString();
    }

    return `${SERVER_REF}/${normalizedRoute}`;
}

export interface AvailableServices {
    REGULAR_BILLS: boolean;
    EMPLOYERS: boolean;
    EMPLOYERS_BENEFITS: boolean;
    CC_REPORT: boolean;
    EMPLOYER_DEPENDENTS: boolean;
    SALES_NF: boolean;
    SERVICE_NF: boolean;
    SERVICE_NF_MANAGER: boolean;
    SERVICE_NF_METADATA_MANAGER: boolean;
}
export const AVALIABLE_SERVICES: AvailableServices = {
    REGULAR_BILLS: true,
    EMPLOYERS: true,
    EMPLOYERS_BENEFITS: true,
    CC_REPORT: true,
    EMPLOYER_DEPENDENTS: true,
    SALES_NF: true,
    SERVICE_NF: true,
    SERVICE_NF_MANAGER: true,
    SERVICE_NF_METADATA_MANAGER: true
};
