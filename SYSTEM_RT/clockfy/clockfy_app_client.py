import json
import os
from datetime import datetime

from dotenv import load_dotenv

from clockfy.clockfy_client import ClockifyClient
from log_jobs.log_jobs import LogJobs
from models import Clock_Client, db

load_dotenv()


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def edit_existing_clock_client(id, data_dict):
    # Get the existing ClockUser instance from the database
    existing_user = get_clock_client_by_id(id)

    # If the user doesn't exist, you might want to handle that case accordingly
    if existing_user is None:
        # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
        return None

    if "name" in data_dict:
        existing_user.name = data_dict["name"]
    if "note" in data_dict:
        existing_user.note = data_dict["note"]

    # Update the 'updated_at' property
    existing_user.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.session.commit()

    return existing_user


def get_clock_client_by_id(id):
    # Replace this with the actual logic to query the database and return the ClockUser instance
    # For example, assuming your ClockUser is stored in a SQLAlchemy database:
    return db.session.query(Clock_Client).filter_by(id=id).first()


def create_clock_client(data_dict):
    new_clock_user = Clock_Client(
        id=data_dict.get("id"),
        name=data_dict.get("name"),
        note=data_dict.get("note"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(new_clock_user)
    db.session.commit()

    return new_clock_user


def is_registers_divergents(reg_db, reg_api):
    if reg_db["name"] != reg_api["name"]:
        return True
    if reg_db["note"] != reg_api["note"]:
        return True
    return False


class ClockifyAppClient:
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

    def query_db_clock_user(self):
        # print("Rodando aqui")
        all_registers = Clock_Client.query.all()
        # Extract column names from the model
        registers_dict_array = []
        for register in all_registers:
            register_dict = {
                "id": register.id,
                "name": register.name,
                "note": register.note,
                "source": "db"
                # Add more fields as needed
            }
            registers_dict_array.append(register_dict)
            self.clockify_all.append(register_dict)
        # print("fromated register", registers_dict_array, flush=True)
        return registers_dict_array
        # print("All registers from here", all_registers, flush=True)

    def get_api_formated_data(self):
        clockfy_client = ClockifyClient()
        clockfy_app_client_data = clockfy_client.api_pages_result(
            f"https://api.clockify.me/api/v1/workspaces/{self.workspace_id}/clients"
        )
        api_registers = []
        for clock_client in clockfy_app_client_data:
            ref = {
                "id": clock_client.get("id"),
                "name": clock_client.get("name"),
                "note": clock_client.get("note"),
                "source": "api",
            }
            api_registers.append(ref)
            self.clockify_all.append(ref)
        return api_registers

    def get_updates(self):
        self.clockify_api_elements = self.get_api_formated_data()
        self.clocikfy_db_elements = self.query_db_clock_user()
        ref = self.clockify_all
        grouped_arrays = group_elements_by_key(ref, "id")

        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    print("O elemento e novo")
                    try:
                        create_clock_client(group[0])
                        log = f"INSERTION OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLOCK_CLIENT", log)
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "CLOCK_CLIENT", f"An error occurred: {e}"
                            )
                        )

            if len(group) == 2:
                ##Precisamos comparar os dois grupos
                if is_registers_divergents(group[0], group[1]):
                    try:
                        edit_existing_clock_client(group[0].get("id"), group[0])
                        log = f"EDIT  OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLOCK_PROJECT", log)
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "CLOCK_PROJECT", f"An error occurred: {e}"
                            )
                        )
        log_jobs = LogJobs()
        log_jobs.post_insertion_update({"logs": self.insertion_logs})
        log_jobs.post_error_update({"logs": self.error_logs})
        return {
            "message": "Clock client update done new",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
