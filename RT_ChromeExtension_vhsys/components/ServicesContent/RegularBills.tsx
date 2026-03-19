import React, { useContext } from 'react';
import ServiceStatus from '../ServiceStatus';
import { DataContext } from '../../context/DataContext';
export default function RelatorioBills() {
    const context = useContext(DataContext);
    return (<div>
            <ServiceStatus service="Despesas recorrentes" service_ref="REGULAR_BILLS"/>
        </div>);
}
