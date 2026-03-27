const axios = require('axios');
const crypto = require('crypto');
const { parse } = require('csv-parse/sync');

class TangerinoTimeEntry {
    constructor(tngWebToken) {
        console.log(`Initializing Tangerino entry for token: ${tngWebToken}`);
        this.authorization = process.env.TANGERINO_TOKEN;
        this.tngWebToken = tngWebToken;
        this.allRegisters = [];
    }


    static createHash(string1, string2) {
        return crypto
            .createHash('sha256')
            .update(string1 + string2)
            .digest('hex');
    }


    static timeToMinutes(timeStr) {
        if (!timeStr || typeof timeStr !== 'string') return 0;
        const match = timeStr.match(/^(\d{2}):(\d{2})$/);
        if (match) {
            const [_, hours, minutes] = match;
            return parseInt(hours) * 60 + parseInt(minutes);
        }
        return 0;
    }

    async fetchTangerinoReport(userId, startDate, endDate) {
        const url = "https://report.tangerino.com.br/async-reports";
        
        const headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "authorization": "MTUxMzY4MjU4OWY5NGY3M2JhYjU2MjM2YjMwZWFlNzE6MmZiNTRiNDc5MDJmNGNjY2E3NDkyMDU0M2QzMGI0ZGE=", // Your fixed auth
            "tng-web-token": this.tngWebToken,
        };

        const body = {
            filter: {
                format: "CSV",
                statusEmployee: "ADMITIDOS",
                startDate: startDate, 
                endDate: endDate,
                employeeId: userId,
            },
            type: "TIME_SHEET",
        };

        try {
            const response = await axios.post(url, body, { headers });
            const fileUrl = response.data.fileUrl;
            console.log(`Report generated. File URL: ${fileUrl}`);
            return fileUrl;
        } catch (error) {
            console.error(`Error fetching report: ${error.response?.data || error.message}`);
            return null;
        }
    }

    async getParsedCsvData(fileUrl) {
        try {
            const response = await axios.get(fileUrl);
            const records = parse(response.data, {
                columns: true,
                skip_empty_lines: true,
                trim: true
            });
            return records;
        } catch (error) {
            console.error(`Error parsing CSV: ${error.message}`);
            return [];
        }
    }

    async processUserReport(userId, start, end) {
        const csvUrl = await this.fetchTangerinoReport(userId, start, end);
        if (!csvUrl) return;

        const data = await this.getParsedCsvData(csvUrl);
        
        const processed = data.map(reg => {
            const dayStr = reg["03 - DIA / MÊS"];
            return {
                ID: TangerinoTimeEntry.createHash(dayStr, String(userId)),
                DAY_REF: dayStr,
                EMPLOYER: reg["01 - NOME"],
                WORKED_MINUTES: TangerinoTimeEntry.timeToMinutes(reg["05 - TRABALHADAS"]),
  
            };
        });

        console.log(`Processed ${processed.length} records.`);
        return processed;
    }
}

module.exports = TangerinoTimeEntry;