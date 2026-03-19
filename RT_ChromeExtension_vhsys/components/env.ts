const DEV_MODE = true
export const SERVER_REF = DEV_MODE
  ? "https://n8n.srv1252717.hstgr.cloud/webhook/8e1d053b-4df1-4cdd-b532-bc6b596a14ed"
  : "https://rt-extension-server-hmbedya2dfh0arg2.canadacentral-01.azurewebsites.net"
export const VERSION = "1.1.1"

export function buildServerRoute(route: string): string {
    const normalizedRoute = route.replace(/^\/+/, "");

    if (DEV_MODE) {
        const webhookUrl = new URL(SERVER_REF);
        webhookUrl.searchParams.set("route", normalizedRoute);
        return webhookUrl.toString();
    }
    

    return `${SERVER_REF}/${normalizedRoute}`;
}
