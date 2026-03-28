import concurrent.futures
import json
import math
import os
import re
import time

import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

ACESS_TOKEN = os.getenv("vhsys_acess_token")
SECRET_ACESS_TOKEN = os.getenv("vhsys_secret_Access_Token")

headers = {
    "access-token": ACESS_TOKEN,
    "secret-access-token": SECRET_ACESS_TOKEN,
    "cache-control": "no-cache",
    "content-type": "application/json",
}


def add_to_rt_system(payload, url):
    headers = {"Content-Type": "application/json"}
    requests.request("POST", url, headers=headers, data=json.dumps(payload), timeout=2)


def get_number_of_registers(url):
    # trunk-ignore(bandit/B113)
    request = requests.get(url, headers=headers)
    request_to_dict = json.loads(request.text)
    return request_to_dict["paging"]["total"]


def extract_cc_value(input_string):
    pattern = re.compile(r"CC[-\s]*(\d+)|CC[-\s]*")

    match = pattern.search(input_string)

    if match and match.group(1):
        return int(match.group(1))
    else:
        return -1


def runBasedInOffset(offset, url):
    headers = {
        "access-token": ACESS_TOKEN,
        "secret-access-token": SECRET_ACESS_TOKEN,
        "cache-control": "no-cache",
        "content-type": "application/json",
    }
    query_params = {
        "offset": offset,
        "limit": 100000,
        "limit_max": 100000,
    }
    response_api = requests.get(
        url,
        headers=headers,
        params=query_params,
        timeout=30,
    )
    response_to_dict = json.loads(response_api.text)
    return response_to_dict


def api_results_by_page_limit(url, max_pages, page_size=100):
    query_results = []

    # Prepare headers for the API request
    headers = {
        "access-token": ACESS_TOKEN,
        "secret-access-token": SECRET_ACESS_TOKEN,
        "cache-control": "no-cache",
        "content-type": "application/json",
    }

    # Use a progress bar to track fetching
    with tqdm(total=max_pages, desc="Fetching API pages", unit=" pages") as pbar:
        for page_num in range(max_pages):
            # Calculate the offset for the current page
            actual_offset = page_num * page_size

            query_params = {
                "offset": actual_offset,
                "limit": page_size,
            }

            try:
                # Make the API request
                response_api = requests.get(
                    url,
                    headers=headers,
                    params=query_params,
                    timeout=10,  # Increased timeout for reliability
                )
                response_api.raise_for_status()  # Check for HTTP errors
                request = response_api.json()

                if not request or request.get("code") != 200:
                    pbar.set_description(
                        f"API Error at offset {actual_offset}. Retrying..."
                    )
                    time.sleep(3)
                    continue

                records_in_batch = request.get("data", [])

                # If the API returns an empty list, it means we've reached the end
                if not records_in_batch:
                    print("\nNo more records available from the API. Stopping early.")
                    # We need to adjust the progress bar to reflect the actual number of pages fetched
                    pbar.total = page_num
                    pbar.refresh()
                    break

                query_results.extend(records_in_batch)
                pbar.update(1)

            except requests.exceptions.RequestException as e:
                print(f"\nRequest for page {page_num + 1} failed: {e}")
                continue  # Skip to the next page on failure

    return query_results


def api_results(url):
    initial_request = runBasedInOffset(0, url)
    # print(f"\n \n Request result {initial_request}")

    if not initial_request or initial_request.get("code") != 200:
        print("Error: Could not fetch initial data from the API.")
        return []

    total_registers = initial_request["paging"]["total"]
    if total_registers == 0:
        print("No records found.")
        return []

    # 3. Start building the results list with data from the first call
    query_results = initial_request["data"]

    # The next offset is based on how many records were in the first batch
    actual_offset = initial_request["paging"]["total_count"]

    # 4. Initialize and manage the progress bar using a 'with' statement
    with tqdm(total=total_registers, desc="Fetching API data", unit=" records") as pbar:
        # The bar is immediately updated with the count from our first API call
        pbar.update(len(query_results))

        # 5. Loop as long as we have more records to fetch
        while actual_offset < total_registers:
            request = runBasedInOffset(actual_offset, url)

            # If a request fails, show a message and pause briefly before continuing
            if not request or request.get("code") != 200:
                pbar.set_description(
                    f"API Error at offset {actual_offset}. Retrying..."
                )
                time.sleep(3)  # Wait 3 seconds before the next attempt
                continue

            records_in_batch = request.get("data", [])

            # If the API returns an empty list of data, it means we're done.
            if not records_in_batch:
                break

            # Add the newly fetched records to our main list
            query_results.extend(records_in_batch)

            # Get the count of items in this specific batch to update the offset and bar
            count_in_batch = request["paging"]["total_count"]

            actual_offset += count_in_batch
            pbar.update(count_in_batch)

            # This ensures the final count on the bar matches the total if the API overshoots
            if pbar.n > total_registers:
                pbar.n = total_registers
                pbar.refresh()

    return query_results


def api_results_parallel(url, max_workers=5):
    try:
        total_registers = get_number_of_registers(url)
        if total_registers == 0:
            print("No records to fetch.")
            return []
        batch_size = 50
        total_pages = math.ceil(total_registers / batch_size)
    except Exception as e:
        print(f"Could not determine total number of pages. Error: {e}")
        return []

    query_results = []
    offsets_to_request = [i * batch_size for i in range(total_pages)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_offset = {
            executor.submit(runBasedInOffset, offset, url, batch_size): offset
            for offset in offsets_to_request
        }

        progress_bar = tqdm(
            concurrent.futures.as_completed(future_to_offset),
            total=len(offsets_to_request),
            desc="Fetching pages in parallel",
        )

        for future in progress_bar:
            try:
                response_data = future.result()
                if response_data and response_data.get("data"):
                    query_results.extend(response_data["data"])
            except Exception as e:
                offset = future_to_offset[future]
                print(f"\nRequest for offset {offset} failed with error: {e}")

    return query_results


def api_list_all(url, datetime_start="01/01/2000"):
    API_DATA = []
    number_of_registers = get_number_of_registers(url)
    print("Number of registers", number_of_registers)
    actual_offset = 0
    while actual_offset <= number_of_registers + 50:
        if actual_offset == 0:
            actual_offset += 49
        else:
            actual_offset += 50
        query_params = {
            "offset": actual_offset,
        }
        print("Query parameters", query_params)
        response_api = requests.get(
            url,
            headers=headers,
            params=query_params,
            timeout=5,
        )
        responses_to_dict = json.loads(response_api.text)
        if isinstance(responses_to_dict["data"], str) is False:
            for response in responses_to_dict["data"]:
                API_DATA.append(response)

    return API_DATA
