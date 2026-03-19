import hashlib
import os
import re
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

from models import Tangerino_entries, db

load_dotenv()


class TangerinoTimeEntry:
    def __init__(self, tng_web_token):
        print(f"Tangerino time entry {tng_web_token}")
        self.authorization = os.getenv("TANGERINO_TOKEN")
        self.tng_web_token = tng_web_token
        self.api_registers = []
        self.all_registers = []
        print(f" \n \n Authorization: {self.authorization}")

    @staticmethod
    def create_hash(string1, string2):
        return hashlib.sha256((string1 + string2).encode("utf-8")).hexdigest()

    @staticmethod
    def time_to_minutes(time_str: str) -> int:
        # Check if the time_str is empty or None
        if not time_str or not isinstance(time_str, str):
            return 0

        # Attempt to match the time format
        match = re.fullmatch(r"(\d{2}):(\d{2})", time_str)
        if match:
            hours, minutes = map(int, match.groups())
            return hours * 60 + minutes
        return 0

    def create_register(self, data):
        new_register = Tangerino_entries(
            ID=data["ID"],
            DAY_REF=data["DAY_REF"],
            DAY=data["DAY"],
            EMPLOYER=data["EMPLOYER"],
            EMPLOYER_CPF=data["EMPLOYER_CPF"],
            worked_hours=data["HORAS_TRABALHADAS"],
            worked_hours_minutes=data["worked_hours_minutes"],
            work_expect=data["HORAS_PREVISTAS"],
            work_expect_minutes=data["work_expect_minutes"],
            TURN_01_START=data["TURN_01_START"],
            TURN_01_END=data["TURN_01_END"],
            TURN_02_START=data["TURN_02_START"],
            TURN_02_END=data["TURN_02_END"],
            TURN_03_START=data["TURN_03_START"],
            TURN_03_END=data["TURN_03_END"],
            TURN_04_START=data["TURN_04_START"],
            TURN_04_END=data["TURN_04_END"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        print(f" \n \n Creating new tangerino entry register  : {data}")
        db.session.add(new_register)
        db.session.commit()

    @staticmethod
    def get_date_before(date_str, days_before):
        date_format = "%Y-%m-%d"
        try:
            given_date = datetime.strptime(date_str, date_format)
            new_date = given_date - timedelta(days=days_before)
            return new_date.strftime(date_format)
        except Exception as e:
            print(f"Error calculating date: {e}")
            return None

    def fetch_tangerino_report(self, user_id, start_date, end_date):
        url = "https://report.tangerino.com.br/async-reports"
        # headers = {
        #     "accept": "application/json, text/plain, */*",
        #     "authorization": self.authorization,
        #     "content-type": "application/json",
        #     "tng-web-token": self.tng_web_token,
        # }

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "access-control-allow-origin": "*",
            "authorization": "MTUxMzY4MjU4OWY5NGY3M2JhYjU2MjM2YjMwZWFlNzE6MmZiNTRiNDc5MDJmNGNjY2E3NDkyMDU0M2QzMGI0ZGE=",
            "content-type": "application/json",
            "tng-web-token": self.tng_web_token,
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
            json_response = response.json()
            print(f"Response JSON: {json_response}")  # Debugging
            file_url = json_response.get("fileUrl")
            print(f"File URL: {file_url}")  # Debugging
            return json_response.get("fileUrl")
        except requests.exceptions.Timeout:
            print(f"Request timed out: {url}")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e} - Response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"General Request Error: {e}")
        return None

    @staticmethod
    def is_csv_empty(file_url):
        try:
            df = pd.read_csv(file_url)
            return False
        except Exception as e:
            print(f"Error reading CSV from {file_url}: {e}")
            return True

    def fetch_employer_data(self):
        url = "https://employer.tangerino.com.br/employee/find-all"
        headers = {"accept": "application/json", "Authorization": self.authorization}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching employer data: {e}")
        return None

    @staticmethod
    def clean_data(record):
        cleaned_record = {}
        for key, value in record.items():
            cleaned_key = key.strip("'").strip('"')
            cleaned_value = value.strip("'").strip('"') if value else ""
            cleaned_record[cleaned_key] = cleaned_value
        return cleaned_record

    @staticmethod
    def get_datetime(date_str, time_str):
        try:
            base_date = datetime.strptime(date_str, "%d/%m/%Y")
            if not time_str.strip():
                return None
            return datetime.combine(
                base_date, datetime.strptime(time_str, "%H:%M").time()
            )
        except ValueError:
            return None

    @staticmethod
    def group_elements_by_key(input_array, key):
        grouped_elements = {}

        for element in input_array:
            element_key = element.get(key)

            if element_key is not None:
                if element_key not in grouped_elements:
                    grouped_elements[element_key] = []

                grouped_elements[element_key].append(element)

        return list(grouped_elements.values())

    @staticmethod
    def delete_register_by_id(id):
        entry_to_delete = db.session.query(Tangerino_entries).filter_by(ID=id).first()

        if entry_to_delete:
            db.session.delete(entry_to_delete)
            db.session.commit()
            return True
        else:
            return False

    def verify_elements_bd(self):
        registers_db = Tangerino_entries.query.all()
        for register in registers_db:
            register_dict = {
                "DAY": register.DAY,
                "DAY_REF": register.DAY_REF,
                "worked_hours_minutes": register.worked_hours_minutes,
                "work_expect_minutes": register.work_expect_minutes,
                "ID": register.ID,
                "EMPLOYER": register.EMPLOYER,
                "EMPLOYER_CPF": register.EMPLOYER_CPF,
                "HORAS_TRABALHADAS": register.worked_hours,
                "HORAS_PREVISTAS": register.work_expect,
                "TURN_01_START": register.TURN_01_START,
                "TURN_01_END": register.TURN_01_END,
                "TURN_02_START": register.TURN_02_START,
                "TURN_02_END": register.TURN_02_END,
                "TURN_03_START": register.TURN_03_START,
                "TURN_03_END": register.TURN_03_END,
                "TURN_04_START": register.TURN_04_START,
                "TURN_04_END": register.TURN_04_END,
                "source": "db",
            }

            self.all_registers.append(register_dict)

    @staticmethod
    def are_registers_divergent(reg_db, reg_api, keys_to_compare):
        for key in keys_to_compare:
            if reg_db[key] != reg_api[key]:
                ref_reg_db = reg_db[key]
                ref_reg_api = reg_api[key]
                print(
                    f"(DIVERGENCES) DB {ref_reg_db} <-> API {ref_reg_api} ,({key}",
                    flush=True,
                )
                return True
        return False

    @staticmethod
    def get_register_by_id(id):
        return db.session.query(Tangerino_entries).filter_by(ID=id).first()

    def edit_existing_register(self, id, data_dict, keys_to_update):
        existing_client = self.get_register_by_id(id)

        if existing_client is None:
            return None

        for key in keys_to_update:
            if key in data_dict:
                setattr(existing_client, key, data_dict[key])

        existing_client.updated_at = datetime.utcnow()

        db.session.commit()

        return existing_client

    def fetch_reports_for_all(self):
        data = self.fetch_employer_data()
        if not data or "content" not in data:
            print("No employee data found.")
            return

        content = data["content"]
        start_limit = datetime.strptime("2000-01-01", "%Y-%m-%d")

        for emp in content:
            emp_id = emp.get("id")
            end_date = datetime.today().strftime("%Y-%m-%d")

            while datetime.strptime(end_date, "%Y-%m-%d") > start_limit:
                start_date = self.get_date_before(end_date, 100)
                if start_date is None:
                    print("Skipping due to invalid date calculation.")
                    break
                if datetime.strptime(start_date, "%Y-%m-%d") < start_limit:
                    start_date = start_limit.strftime("%Y-%m-%d")

                file_url = self.fetch_tangerino_report(emp_id, start_date, end_date)

                if file_url:
                    print("WE HAVE FILE URL")
                    if self.is_csv_empty(file_url):
                        print("THIS URL IS EMPTY")
                        print(
                            f"Empty CSV detected for Employee ID {emp_id}. Skipping to next user."
                        )
                        break
                    df = pd.read_csv(file_url)
                    print(f"OR DF HERE {df}")
                    for reg in df.to_dict(orient="records"):
                        cleaned_reg = self.clean_data(reg)
                        day = cleaned_reg.get("03 - DIA / MÊS")
                        horas_trabalhadas = cleaned_reg.get("05 - TRABALHADAS")
                        horas_previstas = cleaned_reg.get("07 - PREVISTAS")
                        ref = {
                            # "USER_ID": emp_id,
                            "DAY_REF": day,
                            "DAY": datetime.strptime(day, "%d/%m/%Y").strftime(
                                "%Y-%m-%d"
                            ),
                            "ID": self.create_hash(day, str(emp_id)),
                            "EMPLOYER": cleaned_reg.get("01 - NOME"),
                            "EMPLOYER_CPF": cleaned_reg.get("02 - CPF"),
                            "HORAS_TRABALHADAS": horas_trabalhadas,
                            "worked_hours_minutes": self.time_to_minutes(
                                horas_trabalhadas
                            ),
                            "work_expect_minutes": self.time_to_minutes(
                                horas_previstas
                            ),
                            "HORAS_PREVISTAS": horas_previstas,
                            "TURN_01_START": self.get_datetime(
                                day, cleaned_reg.get("09 - TURNO 1 - INICIO")
                            ),
                            "TURN_01_END": self.get_datetime(
                                day, cleaned_reg.get("10 - TURNO 1 - FIM")
                            ),
                            "TURN_02_START": self.get_datetime(
                                day, cleaned_reg.get("11 - TURNO 2 - INICIO")
                            ),
                            "TURN_02_END": self.get_datetime(
                                day, cleaned_reg.get("12 - TURNO 2 - FIM")
                            ),
                            "TURN_03_START": self.get_datetime(
                                day, cleaned_reg.get("13 - TURNO 3 - INICIO")
                            ),
                            "TURN_03_END": self.get_datetime(
                                day, cleaned_reg.get("14 - TURNO 3 - FIM")
                            ),
                            "TURN_04_START": self.get_datetime(
                                day, cleaned_reg.get("15 - TURNO 4 - INICIO")
                            ),
                            "TURN_04_END": self.get_datetime(
                                day, cleaned_reg.get("16 - TURNO 4 - FIM")
                            ),
                            "source": "api",
                        }
                        self.all_registers.append(ref)
                        print(f"\n New ref here {ref}")
                end_date = self.get_date_before(
                    start_date, 1
                )  # Move 1 day back to avoid overlap
                if end_date is None:
                    break

    def update(self):
        keys_array = [
            "DAY_REF",
            "EMPLOYER",
            "EMPLOYER_CPF",
            "HORAS_TRABALHADAS",
            "HORAS_PREVISTAS",
            "TURN_01_START",
            "TURN_01_END",
            "TURN_02_START",
            "TURN_02_END",
            "TURN_03_START",
            "TURN_03_END",
            "TURN_04_START",
            "TURN_04_END",
        ]
        self.fetch_reports_for_all()
        print(" \n \n Dados preenchidos")
        print(f"Elementos da api aqui {self.all_registers} ")
        self.verify_elements_bd()
        grouped_arrays = self.group_elements_by_key(self.all_registers, "ID")
        for group in grouped_arrays:
            if len(group) == 1:
                print(f"Or single element here {group}")
                if group[0].get("source") == "api":
                    try:
                        print("This is for the api")
                        self.create_register(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")
                if group[0].get("source") == "db":
                    ref_id = group[0].get("ID")
                    self.delete_register_by_id(ref_id)

            if len(group) == 2:
                if self.are_registers_divergent(group[1], group[0], keys_array):
                    try:
                        self.edit_existing_register(
                            group[0].get("ID"), group[0], keys_array
                        )
                        print(f" \n \n Temos divergecias group[1]{group[1]}")
                        print(f" \n \n Temos divergecias group[0]{group[0]}")
                    except Exception as e:
                        print(f"An error occurred: {e}")
