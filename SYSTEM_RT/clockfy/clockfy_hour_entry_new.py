import concurrent.futures
import itertools
import json
import logging
import os
import re
import sys
import threading
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
        return round(total_minutes)
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
        if key == "interval_duration_minutes":
            if int(reg_db[key]) != int(reg_api[key]):
                print(f"The key {key} are divergent", flush=True)
                print(f"API {reg_api[key]} -  DB {reg_db[key]}", flush=True)
                print(f"API {reg_api}", flush=True)
                print(f"DB {reg_db}", flush=True)
                return True
        elif reg_db[key] != reg_api[key]:
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


def _spinner(stop_event, message=""):
    """Display a simple loading spinner."""
    spinner = itertools.cycle(["-", "/", "|", "\\"])
    while not stop_event.is_set():
        try:
            sys.stdout.write(f"{message} {next(spinner)}")
            sys.stdout.flush()  # Flush stdout
            time.sleep(0.1)  # Wait
            sys.stdout.write("\b" * (len(message) + 2))
            sys.stdout.flush()
        except (IOError, BrokenPipeError):
            break
        except Exception:
            break
    sys.stdout.write(" " * (len(message) + 2) + "\r")
    sys.stdout.flush()


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
            self.api_genesis.append(time_entry)

            if not tag_id:
                tag_id = "-1"
            else:
                tag_id = tag_id[0]
            if tag_id is None:
                tag_id = "-1"
            convert_iso_to_custom_format(time_entry["timeInterval"].get("start"))
            convert_iso_to_custom_format(time_entry["timeInterval"].get("end"))

            interval_start_moment_brazil_tz = (
                convert_iso_to_custom_format_to_brazil_timezone(
                    time_entry["timeInterval"].get("start")
                )
            )
            interval_end_moment_brazil_tz = (
                convert_iso_to_custom_format_to_brazil_timezone(
                    time_entry["timeInterval"].get("end")
                )
            )

            ref = {
                "id": time_entry.get("id"),
                "description": time_entry.get("description"),
                "tags_id": tag_id,
                "project_id": project_id,
                "interval_start_moment": interval_start_moment_brazil_tz,
                "interval_end_moment": interval_end_moment_brazil_tz,
                "interval_duration": time_entry["timeInterval"].get("duration"),
                "interval_duration_minutes": convert_time_to_minutes(
                    str(interval_duration)
                ),
                "user_id": time_entry.get("userId"),
                "source": "api",
            }
            self.clockify_all.append(ref)
            self.formated_api.append(ref)
            size_of_api_registers = len(self.formated_api)
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

    def _process_group(self, group):
        try:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    entry_data = group[0].copy()
                    entry_data["created_at"] = datetime.utcnow()
                    entry_data["updated_at"] = datetime.utcnow()
                    entry_data.pop("source", None)
                    return ("create", entry_data)

                if group[0].get("source") == "db":
                    ref_id = group[0].get("id")
                    print(f"Marcando para deletar: {ref_id}", flush=True)
                    return ("delete", ref_id)

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

                reg_api = group[0] if group[0]["source"] == "api" else group[1]
                reg_db = group[1] if group[1]["source"] == "db" else group[0]

                if are_registers_divergent(reg_api, reg_db, ref_keys):
                    update_data = reg_api.copy()
                    update_data["updated_at"] = datetime.utcnow()
                    update_data.pop("source", None)
                    return ("update", update_data)

        except Exception as e:
            print(f"Error processing group {group[0].get('id')}: {e}", flush=True)
            return ("error", str(e))

        return (None, None)

    def get_updates(self):
        self.get_optimized_api()
        self.query_db_clock_hour_entry()
        ref = self.clockify_all
        grouped_arrays = group_elements_by_key(ref, "id")

        entries_to_create = []
        ids_to_delete = []
        entries_to_update = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(self._process_group, grouped_arrays)

        for action, data in results:
            if action == "create":
                entries_to_create.append(data)

                log_data = data.copy()
                log_data["created_at"] = log_data["created_at"].isoformat()
                log_data["updated_at"] = log_data["updated_at"].isoformat()

                log = f"INSERTION OF {json.dumps(log_data)}"
                self.insertion_logs.append(
                    self.create_insertion_log("CLOCK_CLIENT", log)
                )
            elif action == "delete":
                ids_to_delete.append(data)
                log = f"DELETION OF ID {data}"
                self.insertion_logs.append(
                    self.create_insertion_log("CLOCK_CLIENT", log)
                )
            elif action == "update":
                entries_to_update.append(data)
                log_data = data.copy()
                log_data["updated_at"] = log_data["updated_at"].isoformat()

                log = f"EDIT OF {json.dumps(log_data)}"
                self.insertion_logs.append(
                    self.create_insertion_log("CLOCK_PROJECT", log)
                )
            elif action == "error":
                self.error_logs.append(
                    self.create_insertion_log("CLOCK_CLIENT_PROCESS", data)
                )

        stop_spinner_event = threading.Event()
        spinner_message = "Committing bulk changes to database..."
        spinner_thread = threading.Thread(
            target=_spinner, args=(stop_spinner_event, spinner_message)
        )
        spinner_thread.start()

        try:
            if entries_to_create:
                print(
                    f"Bulk inserting {len(entries_to_create)} new entries.", flush=True
                )
                db.session.bulk_insert_mappings(Clock_Time_Entry, entries_to_create)

            if ids_to_delete:
                print(f"Bulk deleting {len(ids_to_delete)} old entries.", flush=True)
                db.session.query(Clock_Time_Entry).filter(
                    Clock_Time_Entry.id.in_(ids_to_delete)
                ).delete(synchronize_session=False)

            if entries_to_update:
                print(
                    f"Bulk updating {len(entries_to_update)} divergent entries.",
                    flush=True,
                )
                db.session.bulk_update_mappings(Clock_Time_Entry, entries_to_update)

            print("Committing transaction...", flush=True)
            db.session.commit()
            print("Commit successful.", flush=True)

        except Exception as e:
            print("An error occurred. Rolling back transaction...", flush=True)
            db.session.rollback()
            print(f"An error occurred during bulk DB operations: {e}", flush=True)
            self.error_logs.append(
                self.create_insertion_log(
                    "CLOCK_CLIENT_BULK_OP", f"An error occurred: {e}"
                )
            )
        finally:
            stop_spinner_event.set()
            spinner_thread.join()
            print("Database operations complete.", flush=True)

        return {
            "message": "Clock projects updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
