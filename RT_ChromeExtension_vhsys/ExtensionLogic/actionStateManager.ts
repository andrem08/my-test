import { buildServerRoute } from "./env";
export async function update_action_state<T>(ACTION: string, status: number): Promise<T | null> {
    const url_reference = buildServerRoute("update_services");
    try {
        const bodyData = {
            ACTION: ACTION,
            RUNNING_STATUS: status
        };
        const response = await fetch(url_reference, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(bodyData)
        });
        if (!response.ok) {
            throw new Error(`Failed to post data to ${url_reference}, status: ${response.status}`);
        }
        return await response.json();
    }
    catch (error) {
        console.error("Error in postData:", { url_reference, error });
        return null;
    }
}
