const DEV_MODE = true;

export const SERVER_REF = DEV_MODE
    ? "https://n8n.srv1252717.hstgr.cloud/webhook/795e87e0-f4c1-48c2-9d28-945ddb3eb5ef"
    : "https://rt-extension-server-hmbedya2dfh0arg2.canadacentral-01.azurewebsites.net";
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
 