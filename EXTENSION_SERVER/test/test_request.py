import os
import unittest

import requests
from dotenv import load_dotenv

load_dotenv()


class TestRequisitions(unittest.TestCase):
    def test_orders_update(self):
        URL_REF = "http://127.0.0.1:7000"
        route_ref = "/orders/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_post_nf_report(self):
        data = {
            "cc_id": 123,
            "report_type": "sales",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }
        base_url = "http://127.0.0.1:9005"
        nf_report_url = f"{base_url}/nf_report"
        try:
            print(f"Sending POST request to {nf_report_url} with data: {data}")

            # Make the POST request
            response = requests.post(
                nf_report_url, json=data, headers={"Content-Type": "application/json"}
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Return the response JSON
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during POST request: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    unittest.main()
