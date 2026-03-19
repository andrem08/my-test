import hashlib
import json
import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

from tangerino_time_entry import TangerinoTimeEntry

load_dotenv()

tangerino_entry_route = Blueprint("TANGERINO_ENTRY", __name__)


Authorization = os.getenv("TANGERINO_TOKEN")


def create_hash(string1, string2):
    combined_string = string1 + string2

    hash_object = hashlib.sha256()

    hash_object.update(combined_string.encode("utf-8"))

    return hash_object.hexdigest()


def get_date_before(date_str, days_before):
    date_format = "%Y-%m-%d"
    try:
        given_date = datetime.strptime(date_str, date_format)
        new_date = given_date - timedelta(days=days_before)
        return new_date.strftime(date_format)
    except Exception as e:
        print(f"Error calculating date: {e}")
        return None


def fetch_tangerino_report(user_id, start_date, end_date):
    url = "https://report.tangerino.com.br/async-reports"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "access-control-allow-origin": "*",
        "authorization": "MTUxMzY4MjU4OWY5NGY3M2JhYjU2MjM2YjMwZWFlNzE6MmZiNTRiNDc5MDJmNGNjY2E3NDkyMDU0M2QzMGI0ZGE=",
        "content-type": "application/json",
        "tng-web-token": "eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI5MWI2NjY5ZC1jNTEyLTRlMWEtYjBiOS1kZWVjM2M0N2Y2MDAiLCJpYXQiOjE3NDE2MzA3OTMsInN1YiI6IlNFU1NJT04iLCJpc3MiOiJUTkctV0VCLVRPS0VOIiwiZXhwIjoxNzQxNzE3MTkzLCJ1c2VySWQiOjIwNjcyMTMsInVzZXJUeXBlIjoiQURNSU5JU1RSQVRPUiIsInVzZXJOYW1lIjoiRW3DrWxpbyBIYXJvIiwiZW1wbG95ZXJJZCI6MzkxOTk0OCwiZW1wbG95ZXJFbWFpbCI6ImFtc2lsdmVpcmFAcnRlbmdlbmhhcmlhLmluZC5iciIsInN0YXR1c0FjY291bnQiOiJQYWdhbnRlIC0gQXRpdm8iLCJwYXltZW50VHlwZSI6IkJvbGV0byIsImRhdGVSZWdpc3RlckVtcGxveWVyIjoxNzA5MjQ3MDc3MzY2LCJvcmdhbml6YXRpb25Db2RlIjoiRUUxV1oiLCJlbXBsb3llZUlkIjozOTE5OTQ4LCJlbXBsb3llZU5hbWUiOiJSdCBFbmdlbmhhcmlhIGUgQXV0b21hY2FvIExUREEiLCJlbXBsb3llZVR5cGUiOiJBRE1JTklTVFJBVE9SIn0.9bvRkQrAzgz5b8L4tAKlkLXNApVMLV3CRbIQ7m_O9HA",
    }

    body = {
        "filter": {
            "format": "CSV",
            "statusEmployee": "ADMITIDOS",
            "startDate": start_date,
            "endDate": end_date,
            "employeeId": user_id,
        },
        "type": "TIME_SHEET",
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        response_dict = response.json()
        return response_dict.get("fileUrl")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except json.JSONDecodeError:
        print("Invalid JSON response:", response.text)
    except KeyError:
        print("Unexpected response format:", response.text)

    return None


def is_csv_empty(file_url):
    try:
        df = pd.read_csv(file_url)
        return df.empty
    except Exception as e:
        print(f"Error reading CSV from {file_url}: {e}")
        return True


def fetch_employer_data():
    url = "https://employer.tangerino.com.br/employee/find-all"
    headers = {
        "accept": "application/json;charset=UTF-8",
        "Authorization": Authorization,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching employer data: {e}")
    except json.JSONDecodeError:
        print("Invalid JSON response:", response.text)

    return None


def clean_data(record):
    cleaned_record = {}
    for key, value in record.items():
        cleaned_key = key.strip("'").strip('"')
        cleaned_value = value.strip("'").strip('"') if value else ""
        cleaned_record[cleaned_key] = cleaned_value
    return cleaned_record


def get_datetime(date_str: str, time_str: str):
    try:

        base_date = datetime.strptime(date_str, "%d/%m/%Y")
        if not time_str.strip():
            return None

        time_obj = datetime.strptime(time_str, "%H:%M").time()
        return datetime.combine(base_date, time_obj)

    except ValueError:
        return None


def fetch_reports_for_all():
    data = fetch_employer_data()
    if not data or "content" not in data:
        print("No employee data found.")
        return

    content = data["content"]
    start_limit = datetime.strptime("2020-01-01", "%Y-%m-%d")

    for emp in content:
        emp_id = emp.get("id")

        end_date = datetime.today().strftime("%Y-%m-%d")

        while datetime.strptime(end_date, "%Y-%m-%d") > start_limit:
            start_date = get_date_before(end_date, 1600)
            if start_date is None:
                print("Skipping due to invalid date calculation.")
                break

            if datetime.strptime(start_date, "%Y-%m-%d") < start_limit:
                start_date = start_limit.strftime("%Y-%m-%d")

            file_url = fetch_tangerino_report(emp_id, start_date, end_date)

            if file_url:
                if is_csv_empty(file_url):
                    print(
                        f"Empty CSV detected for Employee ID {emp_id}. Skipping to next user."
                    )
                    break
                df = pd.read_csv(file_url)
                dict_array = df.to_dict(orient="records")
                for reg in dict_array:
                    cleaned_reg = clean_data(reg)
                    DAY = cleaned_reg.get("03 - DIA / MÊS")
                    ref = {
                        "USER_ID": emp_id,
                        "DAY": DAY,
                        "ID": create_hash(DAY, str(emp_id)),
                        "EMPLOYER": cleaned_reg.get("01 - NOME"),
                        "EMPLOYER_CPF": cleaned_reg.get("02 - CPF"),
                        "HORAS_TRABALHADAS": cleaned_reg.get("05 - TRABALHADAS"),
                        "HORAS_PREVISTAS": cleaned_reg.get("07 - PREVISTAS"),
                        "TURN_01_START": get_datetime(
                            DAY, cleaned_reg.get("09 - TURNO 1 - INICIO")
                        ),
                        "TURN_01_END": get_datetime(
                            DAY, cleaned_reg.get("10 - TURNO 1 - FIM")
                        ),
                        "TURN_02_START": get_datetime(
                            DAY, cleaned_reg.get("11 - TURNO 2 - INICIO")
                        ),
                        "TURN_02_END": get_datetime(
                            DAY, cleaned_reg.get("12 - TURNO 2 - FIM")
                        ),
                        "TURN_03_START": get_datetime(
                            DAY, cleaned_reg.get("13 - TURNO 3 - INICIO")
                        ),
                        "TURN_03_END": get_datetime(
                            DAY, cleaned_reg.get("14 - TURNO 3 - FIM")
                        ),
                        "TURN_04_START": get_datetime(
                            DAY, cleaned_reg.get("15 - TURNO 4 - INICIO")
                        ),
                        "TURN_04_END": get_datetime(
                            DAY, cleaned_reg.get("16 - TURNO 4 - FIM")
                        ),
                    }
                    print(f"Or ref here {ref}")

            end_date = get_date_before(start_date, 20)
            if end_date is None:
                break


@tangerino_entry_route.route("/tagerino/time_entry", methods=["PUT"])
def update_tangerino_entries():
    try:
        data = request.get_json()
        print("Request data reference", data)
        web_token = data.get("tangerino_token")
        tangerino_time_entry = TangerinoTimeEntry(web_token)
        tangerino_time_entry.update()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Tangerino data updated successfully"}), 201
