import json
import os
import sys
from datetime import datetime

from alive_progress import alive_bar
from dotenv import load_dotenv

from clockfy.clockfy_client import ClockifyClient
from log_jobs.log_jobs import LogJobs
from models import Clock_User, db

load_dotenv()


# ANSI color codes
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    END = "\033[0m"
    BOLD = "\033[1m"


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def edit_existing_clock_user(user_id, data_dict):
    existing_user = get_clock_user_by_id(user_id)

    if existing_user is None:
        return None

    if "email" in data_dict:
        existing_user.email = data_dict["email"]
    if "name" in data_dict:
        existing_user.name = data_dict["name"]
    if "profile_pic" in data_dict:
        existing_user.profile_pic = data_dict["profile_pic"]
    if "active_workspace" in data_dict:
        existing_user.active_workspace = data_dict["active_workspace"]
    if "default_workspace" in data_dict:
        existing_user.default_workspace = data_dict["default_workspace"]

    existing_user.updated_at = datetime.utcnow()
    db.session.commit()

    return existing_user


def get_clock_user_by_id(user_id):
    return db.session.query(Clock_User).filter_by(id=user_id).first()


def create_clock_user(data_dict):
    new_clock_user = Clock_User(
        id=data_dict.get("id"),
        email=data_dict.get("email"),
        name=data_dict.get("name"),
        profile_pic=data_dict.get("profile_pic"),
        active_workspace=data_dict.get("active_workspace"),
        default_workspace=data_dict.get("default_workspace"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(new_clock_user)
    db.session.commit()

    return new_clock_user


def edit_clock_user(clock_user, data_dict):
    if "id" in data_dict:
        clock_user.id = data_dict["id"]
    if "email" in data_dict:
        clock_user.email = data_dict["email"]
    if "name" in data_dict:
        clock_user.name = data_dict["name"]
    if "profile_pic" in data_dict:
        clock_user.profile_pic = data_dict["profile_pic"]
    if "active_workspace" in data_dict:
        clock_user.active_workspace = data_dict["active_workspace"]
    if "default_workspace" in data_dict:
        clock_user.default_workspace = data_dict["default_workspace"]

    clock_user.updated_at = datetime.utcnow()
    db.session.commit()

    return clock_user


def is_registers_divergents(reg_db, reg_api):
    if reg_db["email"] != reg_api["email"]:
        return True
    if reg_db["name"] != reg_api["name"]:
        return True
    if reg_db["profile_pic"] != reg_api["profile_pic"]:
        return True
    if reg_db["active_workspace"] != reg_api["active_workspace"]:
        return True
    if reg_db["default_workspace"] != reg_api["default_workspace"]:
        return True
    return False


class ClockifyUser:
    def __init__(self):
        self.workspace_id = os.getenv("RT_CLOCKFY_WORKSPACE_ID")
        self.clockify_api_elements = []
        self.clockify_db_elements = []
        self.clockify_all = []
        self.insertion_logs = []
        self.error_logs = []

    def _update_log(self, message, color=None, bold=False):
        """Helper method to update logs with clearing previous line and optional coloring"""
        sys.stdout.write("\r" + " " * 100 + "\r")  # Clear line
        formatted_message = f"\r[STATUS] {message}"

        if color:
            formatted_message = f"{color}{formatted_message}{Colors.END}"
        if bold:
            formatted_message = f"{Colors.BOLD}{formatted_message}{Colors.END}"

        sys.stdout.write(formatted_message + "\n")
        sys.stdout.flush()

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def query_db_clock_user(self):
        self._update_log("Querying database for users...", Colors.BLUE)
        all_registers = Clock_User.query.all()
        registers_dict_array = []

        with alive_bar(
            len(all_registers), title="Formatting DB records", bar="filling"
        ) as bar:
            for register in all_registers:
                register_dict = {
                    "id": register.id,
                    "email": register.email,
                    "name": register.name,
                    "profile_pic": register.profile_pic,
                    "active_workspace": register.active_workspace,
                    "default_workspace": register.default_workspace,
                    "source": "db",
                }
                registers_dict_array.append(register_dict)
                self.clockify_all.append(register_dict)
                bar()
        return registers_dict_array

    def get_api_formated_data(self):
        self._update_log("Fetching user data from Clockify API...", Colors.BLUE)
        clockfy_client = ClockifyClient()
        clockfy_user_data = clockfy_client.api_pages_result(
            f"https://api.clockify.me/api/v1/workspaces/{self.workspace_id}/users"
        )

        api_registers = []
        with alive_bar(
            len(clockfy_user_data), title="Processing API data", bar="filling"
        ) as bar:
            for clock_user in clockfy_user_data:
                ref = {
                    "id": clock_user.get("id"),
                    "email": clock_user.get("email"),
                    "name": clock_user.get("name"),
                    "profile_pic": clock_user.get("profilePicture"),
                    "active_workspace": clock_user.get("activeWorkspace"),
                    "default_workspace": clock_user.get("defaultWorkspace"),
                    "source": "api",
                }
                api_registers.append(ref)
                self.clockify_all.append(ref)
                bar()
        return api_registers

    def get_updates(self):
        # Fetch data with progress indicators
        self.clockify_api_elements = self.get_api_formated_data()
        self.clockify_db_elements = self.query_db_clock_user()

        self._update_log("Grouping and comparing records...", Colors.BLUE)
        ref = self.clockify_all
        grouped_arrays = group_elements_by_key(ref, "id")

        total_groups = len(grouped_arrays)
        with alive_bar(
            total_groups, title="Processing user updates", bar="filling"
        ) as bar:
            for group in grouped_arrays:
                if len(group) == 1:
                    if group[0].get("source") == "api":
                        try:
                            create_clock_user(group[0])
                            log = f"INSERTION OF {json.dumps(group[0])}"
                            self.insertion_logs.append(
                                self.create_insertion_log("CLOCK_USER", log)
                            )
                            self._update_log(
                                f"Created new user: {group[0].get('name')}",
                                Colors.GREEN,
                                bold=True,
                            )
                        except Exception as e:
                            self.error_logs.append(
                                self.create_insertion_log(
                                    "CLOCK_USER", f"An error occurred: {e}"
                                )
                            )
                            self._update_log(
                                f"Error creating user: {e}", Colors.RED, bold=True
                            )

                elif len(group) == 2:
                    if is_registers_divergents(group[0], group[1]):
                        try:
                            edit_existing_clock_user(group[0].get("id"), group[0])
                            log = f"EDIT OF {json.dumps(group[0])}"
                            self.insertion_logs.append(
                                self.create_insertion_log("CLOCK_USER", log)
                            )
                            self._update_log(
                                f"Updated user: {group[0].get('name')}", Colors.YELLOW
                            )
                        except Exception as e:
                            self.error_logs.append(
                                self.create_insertion_log(
                                    "CLOCK_USER", f"An error occurred: {e}"
                                )
                            )
                            self._update_log(
                                f"Error updating user: {e}", Colors.RED, bold=True
                            )
                bar()

        self._update_log("Saving logs to database...", Colors.BLUE)
        log_jobs = LogJobs()
        log_jobs.post_insertion_update({"logs": self.insertion_logs})
        log_jobs.post_error_update({"logs": self.error_logs})

        self._update_log(
            "Clock user update completed successfully!", Colors.GREEN, bold=True
        )
        return {
            "message": "Clock user update done",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
