import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { buildServerRoute } from "~components/env";
import type { AvailableServices } from "../ExtensionLogic/env";
import ServiceRunner from "../ExtensionLogic/updateManager";

interface DataContextType {
    data: any;
    error: string | null;
    firstLoad: boolean;
    runService: (serviceKey: keyof AvailableServices) => Promise<void>;
    entries: number;
    outputs: number;
    total: number;
}

export const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [firstLoad, setFirstLoad] = useState<boolean>(true);
    const [serviceRunner, setServiceRunner] = useState<ServiceRunner | null>(null);
    const [entries, setEntries] = useState<number>(0);
    const [outputs, setOutputs] = useState<number>(0);
    const [total, setTotal] = useState<number>(0);

    useEffect(() => {
        const runner = new ServiceRunner();
        setServiceRunner(runner);
    }, []);

    const fetchData = useCallback(async () => {
        try {
            const response = await fetch(buildServerRoute("get_update_extension_service_data"));
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const result = await response.json();
            setData((prevData) => JSON.stringify(prevData) !== JSON.stringify(result) ? result : prevData);
            setFirstLoad(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        }
    }, []);

    const fetchCCReportData = useCallback(async () => {
        try {
            const response = await fetch(buildServerRoute("cc_report_manage/status"));
            const data = await response.json();
            setEntries(data.number_of_entries);
            setOutputs(data.number_of_outputs);
            setTotal(data.total_lines);
        } catch (error) {
            console.error("Error fetching CC report data:", error);
        }
    }, []);

    const runService = useCallback(async (serviceKey: keyof AvailableServices) => {
        if (serviceRunner) {
            await serviceRunner.run_services(serviceKey);
        }
    }, [serviceRunner]);

    useEffect(() => {
        fetchData();
        fetchCCReportData();
        const interval = setInterval(() => {
            fetchData();
            fetchCCReportData();
        }, 3000);
        return () => clearInterval(interval);
    }, [fetchData, fetchCCReportData]);

    const contextValue = useMemo(() => ({ data, error, firstLoad, runService, entries, outputs, total }), [data, error, firstLoad, runService, entries, outputs, total]);

    return (
        <DataContext.Provider value={contextValue}>
            {children}
        </DataContext.Provider>
    );
};
