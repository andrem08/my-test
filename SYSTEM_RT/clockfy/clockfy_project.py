import json
import os
import re
from datetime import datetime

from dotenv import load_dotenv

from clockfy.clockfy_client import ClockifyClient
from log_jobs.log_jobs import LogJobs
from models import Clock_Project, db
from utils.cost_center_manage import COST_CENTER_MANAGER

load_dotenv()


def extract_first_number(text):
    # Use regular expression to find the first number in the string
    match = re.search(r"\d+", text)

    # If a number is found, return it; otherwise, return -1
    return int(match.group()) if match else -1


def convert_time_to_minutes(time_string):
    # Use regular expression to extract hours, minutes, and optional seconds
    match = re.match(r"PT(\d+)H(?:(\d+)M)?(?:(\d+)S)?", time_string)

    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0

        total_minutes = hours * 60 + minutes + seconds / 60
        return total_minutes
    else:
        return -1


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def edit_existing_clock_project(id, data_dict):
    # Get the existing ClockUser instance from the databasen
    print(" \n \n \n ID HERE", id)
    print(" \n \n \n Editing clock", data_dict, flush=True)
    existing_project = get_clock_project_by_id(id)

    # If the user doesn't exist, you might want to handle that case accordingly
    if existing_project is None:
        # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
        return None

    # Update the instance based on data_dict
    if "name" in data_dict:
        existing_project.name = data_dict["name"]
        # Tambem vai mudar o CC
    if "client_id" in data_dict:
        existing_project.client_id = data_dict["client_id"]
    if "client_name" in data_dict:
        existing_project.client_name = data_dict["client_name"]
    if "duration" in data_dict:
        existing_project.duration = data_dict["duration"]
    if "note" in data_dict:
        existing_project.note = data_dict["note"]
    if "cc_reference" in data_dict:
        existing_project.cc_reference = data_dict["cc_reference"]

    # Update the 'updated_at' property
    existing_project.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.session.commit()

    return existing_project


def get_clock_project_by_id(id):
    # Replace this with the actual logic to query the database and return the ClockUser instance
    # For example, assuming your ClockUser is stored in a SQLAlchemy database:
    return db.session.query(Clock_Project).filter_by(id=id).first()


def create_clock_project(data_dict):
    new_clock_project = Clock_Project(
        id=data_dict.get("id"),
        name=data_dict.get("name"),
        client_id=data_dict.get("client_id"),
        client_name=data_dict.get("client_name"),
        cc_reference=data_dict.get("cc_reference"),
        duration=data_dict.get("duration"),
        duration_minutes=data_dict.get("duration_minutes"),
        note=data_dict.get("note"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(new_clock_project)
    db.session.commit()

    return new_clock_project


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            print(f"The key {key} are divergent", flush=True)
            print("DB reg", reg_db[key], flush=True)
            print("Api reg", reg_api[key], flush=True)
            return True
    return False


class ClockifyProject:
    def __init__(self):
        self.workspace_id = os.getenv("RT_CLOCKFY_WORKSPACE_ID")
        self.clockify_api_elements = []
        self.clockify_db_elements = []
        self.clockify_all = []
        self.insertion_logs = []
        self.error_logs = []

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def query_db_clock_project(self):
        print("Rodando aqui")
        all_registers = Clock_Project.query.all()
        # Extract column names from the model
        registers_dict_array = []
        for register in all_registers:
            register_dict = {
                "id": register.id,
                "cc_reference": str(register.cc_reference),
                "name": register.name,
                "client_id": register.client_id,
                "client_name": register.client_name,
                "duration": register.duration,
                "duration_minutes": register.duration_minutes,
                "note": register.note,
                "source": "db"
                # Add more fields as needed
            }
            registers_dict_array.append(register_dict)
            self.clockify_all.append(register_dict)
        print("fromated register", registers_dict_array, flush=True)
        return registers_dict_array
        print("All registers from here", all_registers, flush=True)

    def get_api_formated_data(self):
        CC_MANAGER = COST_CENTER_MANAGER()
        clockfy_client = ClockifyClient()
        clockfy_user_data = clockfy_client.api_pages_result(
            f"https://api.clockify.me/api/v1/workspaces/{self.workspace_id}/projects"
        )
        print("Clockify user data ", clockfy_user_data)
        api_registers = []
        for clock_client in clockfy_user_data:
            ref = {
                "id": clock_client.get("id"),
                "name": clock_client.get("name"),
                "client_id": clock_client.get("clientId"),
                "client_name": clock_client.get("clientName"),
                "note": clock_client.get("note"),
                "duration": clock_client.get("duration"),
                "duration_minutes": convert_time_to_minutes(
                    clock_client.get("duration")
                ),
                "cc_reference": str(CC_MANAGER.get_cc_label(clock_client.get("name"))),
                "source": "api",
            }
            api_registers.append(ref)
            self.clockify_all.append(ref)
        return api_registers

    def get_updates(self):
        # Precisamos requistar os dados do clockfy
        self.clockify_api_elements = self.get_api_formated_data()
        self.clocikfy_db_elements = self.query_db_clock_project()
        ref = self.clockify_all
        grouped_arrays = group_elements_by_key(ref, "id")
        ref_keys = [
            "name",
            "client_id",
            "client_name",
            "duration",
            "note",
            "cc_reference",
        ]

        for group in grouped_arrays:
            if len(group) == 1:
                print(" \n \n Elemento unico ", group, flush=True)
                print("\n source ", group[0].get("source"))
                if group[0].get("source") == "api":
                    try:
                        create_clock_project(group[0])
                        log = f"INSERTION OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLOCK_PROJECT", log)
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.insertion_logs.append(
                            self.create_insertion_log(
                                "CLOCK_PROJECT", f"An error occurred: {e}"
                            )
                        )
                    print("Aqui estamos")
            if len(group) == 2:
                ##Precisamos comparar os dois grupos
                if are_registers_divergent(group[0], group[1], ref_keys):
                    try:
                        edit_existing_clock_project(group[0].get("id"), group[0])
                        log = f"EDIT  OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLOCK_PROJECT", log)
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.insertion_logs.append(
                            self.create_insertion_log(
                                "CLOCK_PROJECT", f"An error occurred: {e}"
                            )
                        )
        log_jobs = LogJobs()
        log_jobs.post_insertion_update({"logs": self.insertion_logs})
        log_jobs.post_error_update({"logs": self.error_logs})
        return {
            "message": "Clock projects updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
