import logging
import os

import requests
from dotenv import load_dotenv


class LogJobs:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("CLOCKIFY_KEY")
        self.rt_token = os.getenv("RT_TOKEN")
        self.log_server_url = os.getenv("LOG_SERVER_URL")

    def post_insertion_update(self, payloads_ref, batch_size=10):
        payloads = payloads_ref["logs"]
        try:
            if not payloads:
                print("Payloads array is empty. No requests to send.")
                return "Payloads array is empty."

            insertion_url = (
                f"{self.log_server_url}/log/insertion?rt_token={self.rt_token}"
            )

            # Split the payloads into smaller batches
            for i in range(0, len(payloads), batch_size):
                batch = payloads[i : i + batch_size]

                if batch:
                    print("Logs payload batch:", batch)

                    # trunk-ignore(bandit/B113)
                    response = requests.post(insertion_url, json={"logs": batch})

                    # Process the response if needed
                    if response.content:
                        try:
                            result = response.json()
                            print("Response for batch:", result)
                        except ValueError as e:
                            logging.error(f"Error parsing JSON response: {e}")
                    else:
                        print("Empty response received.")

            return "All batches sent successfully"
        except Exception as e:
            logging.error("Error: {0}".format(e))
            return "Error occurred during batch processing"

    def post_error_update(self, payloads_ref, batch_size=10):
        payloads = payloads_ref["logs"]
        try:
            if not payloads:
                print("Payloads array is empty. No requests to send.")
                return "Payloads array is empty."

            insertion_url = f"{self.log_server_url}/log/error?rt_token={self.rt_token}"

            # Split the payloads into smaller batches
            for i in range(0, len(payloads), batch_size):
                batch = payloads[i : i + batch_size]

                if batch:
                    print("Logs payload batch:", batch)

                    # trunk-ignore(bandit/B113)
                    response = requests.post(insertion_url, json={"logs": batch})

                    # Process the response if needed
                    if response.content:
                        try:
                            result = response.json()
                            print("Response for batch:", result)
                        except ValueError as e:
                            logging.error(f"Error parsing JSON response: {e}")
                    else:
                        print("Empty response received.")

            return "All batches sent successfully"
        except Exception as e:
            logging.error("Error: {0}".format(e))
            return "Error occurred during batch processing"
