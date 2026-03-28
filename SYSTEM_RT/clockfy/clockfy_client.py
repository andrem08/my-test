import os

import requests
from dotenv import load_dotenv

#Teste de Descrição de Função - Damarques

class ClockifyClient:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("CLOCKIFY_KEY")
        self.headers = {"X-Api-Key": self.api_key}
        self.api_result = []

    def api_pages_result(self, url):
        size = 1
        i = 1
        while size != 0:
            clockfy_requests_data = self.request_get(f"{url}?page={i}&page-size=4000")
            for req_element in clockfy_requests_data:
                self.api_result.append(req_element)
            size = len(clockfy_requests_data)
            i += 1
        return self.api_result

    def request_get(self, url):
        # trunk-ignore(trunk/ignore-disabled-linter)
        # trunk-ignore(bandit/B113)
        response = requests.get(url, headers=self.headers)
        return response.json()

    def request_post(self, url, payload):
        # trunk-ignore(bandit/B113)
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
