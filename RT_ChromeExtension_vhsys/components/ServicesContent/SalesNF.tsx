import React, { useState, useEffect, useMemo } from 'react';
import ServiceStatus from '../ServiceStatus';
export default function SalesNF() {
    const handleRunService = () => {
        chrome.runtime.sendMessage({ action: "runService", service: "EMPLOYERS" });
    };
    return (<div>
      <ServiceStatus service="Relatorio de notas vendas" service_ref="SALES_NF"/>
        </div>);
}
