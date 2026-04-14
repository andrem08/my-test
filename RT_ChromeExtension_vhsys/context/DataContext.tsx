import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { buildServerRoute } from "~components/env";
import type { AvailableServices } from "../ExtensionLogic/env";
import ServiceRunner from "../ExtensionLogic/updateManager";

export type CCReportScope = "all" | "last_3_months";
export type CCReportAction = "CC_REPORT" | "CC_REPORT_3_MONTHS";

type ServiceStatusItem = {
    ACTION: string;
    RUN_STATUS: number;
};

type CCStatusTotals = {
    entries: number;
    outputs: number;
    total: number;
};

const CC_GENERAL_ACTION: CCReportAction = "CC_REPORT";
const CC_3_MONTHS_ACTION: CCReportAction = "CC_REPORT_3_MONTHS";

const EMPTY_CC_TOTALS: CCStatusTotals = {
    entries: 0,
    outputs: 0,
    total: 0
};

function scopeToAction(scope: CCReportScope): CCReportAction {
    return scope === "last_3_months" ? CC_3_MONTHS_ACTION : CC_GENERAL_ACTION;
}

function resolveCCDisplayAction(
    scope: CCReportScope,
    data: ServiceStatusItem[] | null
): CCReportAction {
    const items = Array.isArray(data) ? data : [];
    const byAction = new Map(items.map((item) => [item.ACTION, item.RUN_STATUS]));

    if (byAction.get(CC_3_MONTHS_ACTION) === 1) return CC_3_MONTHS_ACTION;
    if (byAction.get(CC_GENERAL_ACTION) === 1) return CC_GENERAL_ACTION;

    return scopeToAction(scope);
}

interface DataContextType {
    data: ServiceStatusItem[] | null;
    error: string | null;
    firstLoad: boolean;
    runService: (serviceKey: keyof AvailableServices) => Promise<void>;
    entries: number;
    outputs: number;
    total: number;
    ccReportScope: CCReportScope;
    setCCReportScope: React.Dispatch<React.SetStateAction<CCReportScope>>;
    ccDisplayAction: CCReportAction;
    ccSummaryEntries: number;
    ccSummaryOutputs: number;
    ccSummaryTotal: number;
}

export const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [data, setData] = useState<ServiceStatusItem[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [firstLoad, setFirstLoad] = useState<boolean>(true);
    const [serviceRunner, setServiceRunner] = useState<ServiceRunner | null>(null);
    const [entries, setEntries] = useState<number>(0);
    const [outputs, setOutputs] = useState<number>(0);
    const [total, setTotal] = useState<number>(0);
    const [ccTotalsAll, setCCTotalsAll] = useState<CCStatusTotals>(EMPTY_CC_TOTALS);
    const [ccTotalsLast3Months, setCCTotalsLast3Months] = useState<CCStatusTotals>(EMPTY_CC_TOTALS);
    const [ccReportScope, setCCReportScope] = useState<CCReportScope>("all");
    const buildCCStatusRoute = useCallback((scope: CCReportScope): string => {
        if (scope === "last_3_months") {
            const url = new URL(buildServerRoute("cc_report_manage/status"));
            url.searchParams.set("months_back", "3");
            return url.toString();
        }

        return buildServerRoute("cc_report_manage/status");
    }, []);


    useEffect(() => {
        const runner = new ServiceRunner();
        setServiceRunner(runner);
        void runner.resumeRunningServices();
    }, []);

    const fetchData = useCallback(async () => {
        try {
            const response = await fetch(buildServerRoute("get_update_extension_service_data"));
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const result = await response.json();
            const parsedResult = Array.isArray(result) ? (result as ServiceStatusItem[]) : [];
            setData((prevData) => JSON.stringify(prevData) !== JSON.stringify(parsedResult) ? parsedResult : prevData);
            setFirstLoad(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        }
    }, []);

    const fetchCCReportData = useCallback(async () => {
        try {
            const statusUrl = buildCCStatusRoute(ccReportScope);
            const response = await fetch(statusUrl);

            if (!response.ok) {
                throw new Error(`HTTP error! status=${response.status}`);
            }

            const statusData = await response.json();

            const parsedTotals: CCStatusTotals = {
                entries: Number(statusData.number_of_entries || 0),
                outputs: Number(statusData.number_of_outputs || 0),
                total: Number(statusData.total_lines || 0)
            };

            if (ccReportScope === "last_3_months") {
                setCCTotalsLast3Months(parsedTotals);
            } else {
                setCCTotalsAll(parsedTotals);
            }

            setEntries(parsedTotals.entries);
            setOutputs(parsedTotals.outputs);
            setTotal(parsedTotals.total);
        } catch (error) {
            console.error("Error fetching CC report data:", error);
            setEntries(0);
            setOutputs(0);
            setTotal(0);

            if (ccReportScope === "last_3_months") {
                setCCTotalsLast3Months(EMPTY_CC_TOTALS);
            } else {
                setCCTotalsAll(EMPTY_CC_TOTALS);
            }
        }
    }, [buildCCStatusRoute, ccReportScope]);

    useEffect(() => {
        if (!data || data.length === 0) return;

        const running3Months = data.some(
            (item) => item.ACTION === "CC_REPORT_3_MONTHS" && item.RUN_STATUS === 1
        );
        const runningGeneral = data.some(
            (item) => item.ACTION === "CC_REPORT" && item.RUN_STATUS === 1
        );

        if (running3Months && ccReportScope !== "last_3_months") {
            setCCReportScope("last_3_months");
            return;
        }

        if (runningGeneral && !running3Months && ccReportScope !== "all") {
            setCCReportScope("all");
        }
    }, [data, ccReportScope]);

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

    const ccSummaryTotals = useMemo<CCStatusTotals>(() => {
        return ccReportScope === "last_3_months"
            ? ccTotalsLast3Months
            : ccTotalsAll;
    }, [ccReportScope, ccTotalsAll, ccTotalsLast3Months]);

    const ccDisplayAction = useMemo<CCReportAction>(() => {
        return resolveCCDisplayAction(ccReportScope, data);
    }, [ccReportScope, data]);

    const contextValue = useMemo(() => ({
        data,
        error,
        firstLoad,
        runService,
        entries,
        outputs,
        total,
        ccReportScope,
        setCCReportScope,
        ccDisplayAction,
        ccSummaryEntries: ccSummaryTotals.entries,
        ccSummaryOutputs: ccSummaryTotals.outputs,
        ccSummaryTotal: ccSummaryTotals.total
    }), [
        data,
        error,
        firstLoad,
        runService,
        entries,
        outputs,
        total,
        ccReportScope,
        ccDisplayAction,
        ccSummaryTotals
    ]);

    return (
        <DataContext.Provider value={contextValue}>
            {children}
        </DataContext.Provider>
    );
};
