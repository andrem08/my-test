const DEV_MODE = true
export const SERVER_REF = DEV_MODE
  ? "https://n8n.srv1252717.hstgr.cloud/webhook/vhsys-router"
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
