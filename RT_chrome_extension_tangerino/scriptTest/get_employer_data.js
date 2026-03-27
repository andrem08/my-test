const fetchEmployerData = async () => {
    const url = "https://employer.tangerino.com.br/employee/find-all";
    
    const headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "access-control-allow-origin": "*",
        "authorization": "MTUxMzY4MjU4OWY5NGY3M2JhYjU2MjM2YjMwZWFlNzE6MmZiNTRiNDc5MDJmNGNjY2E3NDkyMDU0M2QzMGI0ZGE=",
        "content-type": "application/json",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "tng-web-token": "eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJjMTQwZTQxNC1iMjYzLTQ5NGEtYTQ0MS1iMThmM2MyM2YwMzAiLCJpYXQiOjE3NzM5Mzg4NzEsInN1YiI6IlNFU1NJT04iLCJpc3MiOiJUTkctV0VCLVRPS0VOIiwiZXhwIjoxNzc0MDI1MjcxLCJ1c2VySWQiOjIwNjcyMTMsInVzZXJUeXBlIjoiQURNSU5JU1RSQVRPUiIsInVzZXJOYW1lIjoiRW3DrWxpbyBIYXJvIiwiZW1wbG95ZXJJZCI6MzkxOTk0OCwiZW1wbG95ZXJFbWFpbCI6ImFtc2lsdmVpcmFAcnRlbmdlbmhhcmlhLmluZC5iciIsInN0YXR1c0FjY291bnQiOiJQYWdhbnRlIC0gQXRpdm8iLCJwYXltZW50VHlwZSI6IkJvbGV0byIsImRhdGVSZWdpc3RlckVtcGxveWVyIjoxNzA5MjQ3MDc3MzY2LCJvcmdhbml6YXRpb25Db2RlIjoiRUUxV1oiLCJlbXBsb3llZUlkIjozOTE5OTQ4LCJlbXBsb3llZU5hbWUiOiJSdCBFbmdlbmhhcmlhIGUgQXV0b21hY2FvIExUREEiLCJlbXBsb3llZVR5cGUiOiJBRE1JTklTVFJBVE9SIn0.BTCyv4hI-j-5mF6AcDpxz4MlWvaTtZeqLQ7j0AAoVdI",
        "Referer": "https://report-web.tangerino.com.br/",
    };

    console.log(`Authorization here ${headers.authorization}`);

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        if (error instanceof SyntaxError) {
            console.error("Invalid JSON response.");
        } else {
            console.error(`Error fetching employer data: ${error.message}`);
        }
    }
};

fetchEmployerData().then(data => console.log(data));