const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { finished } = require('stream/promises');
const dfd = require("danfojs-node");

class TangerinoReportManager {
    constructor() {
        this.executionStartTime = Date.now();
        this.token = fs.readFileSync(path.join(__dirname, 'token.txt'), 'utf8').trim();
        this.authorization = fs.readFileSync(path.join(__dirname, 'authorization.txt'), 'utf8').trim();
        
        this.generate_report_response = null;
        this.repost_list_response = null;

        this.client = axios.create({
            baseURL: "https://report.tangerino.com.br",
            headers: {
                "Content-Type": "application/json",
                "tng-web-token": this.token,
                "authorization": this.authorization
            }
        });
    }

    _format(ms) {
        return ms ? new Date(ms).toLocaleString('pt-BR') : null;
    }

    async downloadReport(url, fileName) {
        if (!url) throw new Error("No URL provided for download.");

        const destination = path.join(__dirname, fileName);
        const writer = fs.createWriteStream(destination);

        const response = await axios({
            method: 'get',
            url: url,
            responseType: 'stream',
        });

        response.data.pipe(writer);
        await finished(writer);
        
        console.log(`✅ File: ${destination}`);
        return destination;
    }

    async generateReport() {
        const today = new Date().toISOString().split('T')[0];
        const payload = {
            filter: {
                format: "CSV",
                statusEmployee: "ADMITIDOS",
                startDate: "2026-01-01",
                endDate: today,
                employee: { "id": null, "name": "Todos" }
            },
            type: "TIME_SHEET"
        };
        const response = await this.client.post("/async-reports", payload);
        this.generate_report_response = response.data;
        return JSON.stringify(this.generate_report_response, null, 2);
    }

    async getHistory() {
        const response = await this.client.get("/history", { params: { size: 10, page: 1 } });
        const rawData = response.data;
        const filteredList = rawData.list.filter(item => item.startAt > this.executionStartTime);

        const processedList = filteredList.map(item => ({
            ...item,
            startAtFormatted: this._format(item.startAt),
            finishAtFormatted: this._format(item.finishAt),
            referenceStartFormatted: this._format(item.referenceStart),
            referenceEndFormatted: this._format(item.referenceEnd)
        }));

        this.repost_list_response = { ...rawData, list: processedList, totalFiltered: processedList.length };
        return JSON.stringify(this.repost_list_response, null, 2);
    }
}


async function getReportAsJSON(url) {
    if (!url) throw new Error("No URL provided.");

    try {
        const df = await dfd.readCSV(url);
        let rawData = dfd.toJSON(df);

        const cleanData = rawData.map(row => {
            const newRow = {};
            for (let key in row) {
                const cleanKey = key.replace(/^'|'$/g, '');
                const cleanValue = String(row[key]).replace(/^'|'$/g, '');
                newRow[cleanKey] = cleanValue === "" ? null : cleanValue;
            }
            return newRow;
        });

        console.log(`✅ Data cleaned. First key example: ${Object.keys(cleanData[0])[0]}`);
        return cleanData; 
    } catch (error) {
        console.error("Failed to parse CSV:", error.message);
        throw error;
    }
}


async function run() {
    const manager = new TangerinoReportManager();

    try {
        await manager.generateReport();
        
        console.log("Waiting 10s...");
        await new Promise(r => setTimeout(r, 10000));

        await manager.getHistory();
        
        const newReports = manager.repost_list_response.list;

        if (newReports.length > 0 && newReports[0].url) {
            const latestReport = newReports[0];
            const data_as_json = await getReportAsJSON(newReports[0].url);
            console.log("Data as json", data_as_json)
        } else {
            console.log("⚠️ No URL found.");
        }

    } catch (error) {
        console.error("Error:", error.message);
    }
}

run();