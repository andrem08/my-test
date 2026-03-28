import concurrent.futures
import json
import logging
import os
import re
import time
from datetime import datetime

import pytz
import requests
from dotenv import load_dotenv

from clockfy.clockfy_client import ClockifyClient
from models import (
    Clock_Project,
    Clock_tag,
    Clock_Time_Entry,
    Clock_User,
    Contexted_hour_entry,
    db,
)

load_dotenv()


def check_or_create_id(id):
    existing_instance = Clock_tag.query.filter_by(id=id).first()

    if existing_instance:
        return id
    else:
        new_instance = Clock_tag(
            id=id,
            name="EMPTY",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(new_instance)
        db.session.commit()
        return id


def verify_trunked_project(id):
    existing_instance = Clock_Project.query.filter_by(id=id).first()

    if existing_instance:
        return id
    else:
        new_instance = Clock_Project(
            id=id,
            name="NO_PROJECT",
            client_id="-1",
            client_name="-1",
            cc_reference="-1",
            duration="-1",
            duration_minutes=0,
            note="NO PROJECT REFERENCE",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(new_instance)
        db.session.commit()
        return id


def save_dict_to_json(data, filename):
    with open(filename, "w") as json_file:
        json.dump(data, json_file)


def extract_first_number(text):
    match = re.search(r"\d+", text)
    return int(match.group()) if match else -1


def convert_time_to_minutes(time_string):
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", time_string)
    if match:
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        total_minutes = hours * 60 + minutes + seconds / 60
        return total_minutes
    else:
        return 0


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)
        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def get_contexted_hour_id(id):
    return db.session.query(Contexted_hour_entry).filter_by(ORIGEM_ID=id).first()


def edit_existing_contexted_hour(id, data_dict, keys_to_update):
    existing_element = get_contexted_hour_id(id)
    if existing_element is None:
        return None

    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_element, key, data_dict[key])

    existing_element.updated_at = datetime.utcnow()

    db.session.commit()

    return existing_element


def edit_existing_clock_hour_entry(id, data_dict):
    print(f"Editing data here {data_dict}", flush=True)
    existing_clock_entry = get_clock_hour_entry_by_id(id)
    if existing_clock_entry is None:
        return None
    if "description" in data_dict:
        existing_clock_entry.description = data_dict["description"]
    if "tags_id" in data_dict:
        existing_clock_entry.tags_id = data_dict["tags_id"]
    if "interval_start_moment" in data_dict:
        existing_clock_entry.interval_start_moment = data_dict["interval_start_moment"]
    if "interval_end_moment" in data_dict:
        existing_clock_entry.interval_end_moment = data_dict["interval_end_moment"]
    if "user_id" in data_dict:
        existing_clock_entry.user_id = data_dict["user_id"]
    if "interval_duration" in data_dict:
        existing_clock_entry.interval_duration = data_dict["interval_duration"]
    if "interval_duration_minutes" in data_dict:
        existing_clock_entry.interval_duration_minutes = data_dict[
            "interval_duration_minutes"
        ]
    if "project_id" in data_dict:
        existing_clock_entry.project_id = data_dict["project_id"]
    existing_clock_entry.updated_at = datetime.utcnow()
    db.session.commit()
    return existing_clock_entry


def delete_clock_hour_entry_by_id(id):
    entry_to_delete = db.session.query(Clock_Time_Entry).filter_by(id=id).first()

    if entry_to_delete:
        db.session.delete(entry_to_delete)
        db.session.commit()
        return True
    else:
        return False


def convert_iso_to_custom_format_to_brazil_timezone(iso_string):
    try:
        datetime_obj = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        brt_timezone = pytz.timezone("America/Sao_Paulo")
        datetime_obj = datetime_obj.replace(tzinfo=pytz.utc).astimezone(brt_timezone)
        formatted_string = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

        return formatted_string
    except ValueError:
        print("Invalid ISO format provided.", flush=True)
        return None


def convert_iso_to_custom_format(iso_string):
    try:
        datetime_obj = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        formatted_string = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_string
    except ValueError:
        print("Invalid ISO format provided.", flush=True)
        return None


def format_datetime_to_string(datetime_obj):
    formatted_string = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_string


def get_clock_hour_entry_by_id(id):
    return db.session.query(Clock_Time_Entry).filter_by(id=id).first()


def create_clock_hour_entry(data_dict):
    try:
        new_clock_time_entry = Clock_Time_Entry(
            id=data_dict.get("id"),
            description=data_dict.get("description"),
            user_id=data_dict.get("user_id"),
            project_id=data_dict.get("project_id"),
            tags_id=data_dict.get("tags_id"),
            interval_start_moment=data_dict.get("interval_start_moment"),
            interval_end_moment=data_dict.get("interval_end_moment"),
            interval_duration=data_dict.get("interval_duration"),
            interval_duration_minutes=data_dict.get("interval_duration_minutes"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(new_clock_time_entry)
        db.session.commit()
        print("Inserindo o registro ", data_dict, flush=True)
        return new_clock_time_entry
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def is_registers_divergents(reg_db, reg_api):
    if reg_db["description"] != reg_api["description"]:
        return True
    if reg_db["tags_id"] != reg_api["tags_id"]:
        return True
    if reg_db["interval_start_moment"] != reg_api["interval_start_moment"]:
        return True
    if reg_db["interval_start_moment"] != reg_api["interval_start_moment"]:
        return True
    if reg_db["project_id"] != reg_api["project_id"]:
        return True
    if reg_db["duration"] != reg_api["duration"]:
        return True
    if reg_db["note"] != reg_api["note"]:
        return True
    return False


def are_registers_divergent(reg_api, reg_db, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            print(f"The key {key} are divergent", flush=True)
            print(f"API {reg_api[key]} -  DB {reg_db[key]}", flush=True)
            print(f"API {reg_api}", flush=True)
            print(f"DB {reg_db}", flush=True)
            return True
    return False


def request_get(url):
    load_dotenv()
    api_key = os.getenv("CLOCKIFY_KEY")
    headers = {"X-Api-Key": api_key}
    while True:
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            logging.error("Error: {0}".format(e))
            logging.error("Try again in 60 seconds")
            time.sleep(60)


def api_pages_result(url):
    size = 1
    i = 1
    result = []
    while size != 0:
        clockfy_requests_data = request_get(f"{url}?page={i}&page-size=5000")
        for req_element in clockfy_requests_data:
            result.append(req_element)
        size = len(clockfy_requests_data)
        i += 1
    return result


class ClockifyHourEntry:
    def __init__(self):
        load_dotenv()
        self.workspace_id = os.getenv("RT_CLOCKFY_WORKSPACE_ID")
        self.clockify_api_elements = []
        self.clockify_db_elements = []
        self.clockify_user_elements = []
        self.clockify_all = []
        self.insertion_logs = []
        self.error_logs = []
        self.clockify_client = ClockifyClient()
        self.api_genesis = []
        self.formated_api = []

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def query_db_clock_user(self):
        all_registers = Clock_User.query.all()
        for register in all_registers:
            register_dict = {
                "id": register.id,
            }
            self.clockify_user_elements.append(register_dict)

    def query_db_clock_hour_entry(self):
        all_registers = Clock_Time_Entry.query.all()
        for register in all_registers:
            register_dict = {
                "id": register.id,
                "description": register.description,
                "tags_id": register.tags_id,
                "project_id": register.project_id,
                "interval_start_moment": format_datetime_to_string(
                    register.interval_start_moment
                ),
                "interval_end_moment": format_datetime_to_string(
                    register.interval_end_moment
                ),
                "interval_duration": register.interval_duration,
                "interval_duration_minutes": register.interval_duration_minutes,
                "user_id": register.user_id,
                "project": register.project,
                "source": "db",
            }
            self.clockify_all.append(register_dict)
            self.clockify_db_elements.append(register_dict)

    def fetch_time_entries(self, user_id):
        time_entries = api_pages_result(
            f"https://api.clockify.me/api/v1/workspaces/{self.workspace_id}/user/{user_id}/time-entries"
        )
        refs = []
        for time_entry in time_entries:
            project_id = "-1"
            if time_entry.get("projectId") is not None:
                project_id = time_entry.get("projectId")
            interval_duration = time_entry["timeInterval"].get("duration")
            tag_id = time_entry.get("tagIds")
            print(f"\n api genesis {time_entry}", flush=True)
            self.api_genesis.append(time_entry)

            if not tag_id:
                tag_id = "-1"
            else:
                tag_id = tag_id[0]
            if tag_id is None:
                tag_id = "-1"

            convert_iso_to_custom_format(time_entry["timeInterval"].get("start"))
            convert_iso_to_custom_format(time_entry["timeInterval"].get("end"))

            (
                convert_iso_to_custom_format_to_brazil_timezone(
                    time_entry["timeInterval"].get("start")
                )
            )
            (
                convert_iso_to_custom_format_to_brazil_timezone(
                    time_entry["timeInterval"].get("end")
                )
            )

            ref = {
                "id": time_entry.get("id"),
                "description": time_entry.get("description"),
                "tags_id": tag_id,
                "project_id": project_id,
                "interval_start_moment": convert_iso_to_custom_format(
                    time_entry["timeInterval"].get("start")
                ),
                "interval_end_moment": convert_iso_to_custom_format(
                    time_entry["timeInterval"].get("end")
                ),
                "interval_duration": time_entry["timeInterval"].get("duration"),
                "interval_duration_minutes": convert_time_to_minutes(
                    str(interval_duration)
                ),
                "user_id": time_entry.get("userId"),
                "source": "api",
            }
            self.clockify_all.append(ref)
            self.formated_api.append(ref)
            refs.append(ref)

        return refs

    def get_optimized_api(self):
        self.query_db_clock_user()
        user_ids = []
        for user in self.clockify_user_elements:
            user_ids.append(user.get("id"))
        time_entries = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.fetch_time_entries, user_id)
                for user_id in user_ids
            ]
            concurrent.futures.wait(futures)

        return time_entries

    def get_api(self):
        self.get_optimized_api()

        return self.formated_api

    def get_updates(self):
        self.get_optimized_api()
        self.query_db_clock_hour_entry()
        ref = self.clockify_all
        grouped_arrays = group_elements_by_key(ref, "id")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        create_clock_hour_entry(group[0])
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
                if group[0].get("source") == "db":
                    ref_id = group[0].get("id")
                    print(f"Vamos deletar nossos registro {ref_id} aqui", flush=True)
                    delete_clock_hour_entry_by_id(ref_id)
            if len(group) == 2:
                ref_keys = [
                    "description",
                    "tags_id",
                    "project_id",
                    "interval_start_moment",
                    "interval_end_moment",
                    "interval_duration",
                    "interval_duration_minutes",
                    "user_id",
                ]
                if are_registers_divergent(group[0], group[1], ref_keys):
                    try:
                        edit_existing_clock_hour_entry(group[0].get("id"), group[0])
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
        return {
            "message": "Clock projects updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
