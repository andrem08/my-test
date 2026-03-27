const splitDateInterval = (startStr, endStr, segments) => {
    const start = new Date(startStr);
    const end = new Date(endStr);
    
    const totalDays = Math.floor((end - start) / (1000 * 60 * 60 * 24));
    const daysPerSegment = Math.floor(totalDays / segments);
    
    return Array.from({ length: segments }, (_, i) => {
        const periodStart = new Date(start);
        periodStart.setDate(start.getDate() + (i * daysPerSegment) + (i > 0 ? 1 : 0));

        let periodEnd = new Date(start);
        if (i === segments - 1) {
            periodEnd = new Date(end);
        } else {
            periodEnd.setDate(start.getDate() + ((i + 1) * daysPerSegment));
        }

        return {
            start: periodStart.toISOString().split('T')[0],
            end: periodEnd.toISOString().split('T')[0]
        };
    });
};


const splited_data = splitDateInterval("2025-01-01","2026-01-01",5)
console.log("Or splited data here", splited_data)