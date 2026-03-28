import os
from datetime import datetime

from dotenv import load_dotenv

from clockfy.clockfy_client import ClockifyClient
from models import Clock_tag, db

load_dotenv()


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)
        # print("Gruping array here", flush=True)
        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def edit_existing_clock_tag(id, data_dict):
    # Get the existing ClockUser instance from the database
    existing_tag = get_tag_by_id(id)

    # If the user doesn't exist, you might want to handle that case accordingly
    if existing_tag is None:
        # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
        return None

    # Update the instance based on data_dict
    if "id" in data_dict:
        existing_tag.id = data_dict["id"]
    if "name" in data_dict:
        existing_tag.name = data_dict["name"]

    # Update the 'updated_at' property
    existing_tag.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.session.commit()

    return existing_tag


def get_tag_by_id(id):
    return db.session.query(Clock_tag).filter_by(id=id).first()

def delete_clock_tag_by_id(id):
    if(id == "-1"):
        return True
    entry_to_delete = get_tag_by_id(id)
    print(f"\n \n Deleting this clock element {entry_to_delete}")

    if entry_to_delete:
        db.session.delete(entry_to_delete)
        db.session.commit()
        return True
    else:
        return False


def create_clock_user(data_dict):
    print("Passou por aqui")
    new_clock_user = Clock_tag(
        id=data_dict.get("id"),
        name=data_dict.get("name"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(new_clock_user)
    db.session.commit()

    return new_clock_user


def edit_tag(id, data_dict):

    existing_instance = Clock_tag.query.filter_by(id=id).first()

    if "name" in data_dict:
        existing_instance.id = data_dict["name"]
    existing_instance.updated_at = datetime.utcnow()
    db.session.commit()
    return existing_instance


def is_registers_divergents(reg_db, reg_api):
    if reg_db["id"] != reg_api["id"]:
        return True
    if reg_db["name"] != reg_api["name"]:
        return True
    return False


class ClockifyTags:
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
        all_registers = Clock_tag.query.all()
        # Extract column names from the model
        for register in all_registers:
            register_dict = {
                "id": register.id,
                "name": register.name,
                "source": "db"
                # Add more fields as needed
            }
            print(f"\n Registers {register}")
            print(f"\n register model {register_dict} ")
            # registers_dict_array.append(register_dict)
            self.clockify_all.append(register_dict)


    def get_api_formated_data(self):
        clockfy_client = ClockifyClient()
        clockfy_tags = clockfy_client.api_pages_result(
            f"https://api.clockify.me/api/v1/workspaces/{self.workspace_id}/tags"
        )
        print(f"\n \n Clock tags here {clockfy_tags}")
        for clock_tag in clockfy_tags:
            print(f"\n \n Clocktag {clock_tag}")
            ref = {
                "id": clock_tag.get("id"),
                "name": clock_tag.get("name"),
                "source": "api",
            }
            # api_registers.append(ref)
            self.clockify_all.append(ref)
        # return api_registers

    def get_updates(self):
        self.clockify_api_elements = self.get_api_formated_data()
        self.clocikfy_db_elements = self.query_db_clock_user()
        self.clockify_all.append({
                "id": "-1",
                "name": "NO_TAG",
                "source": "api"
                # Add more fields as needed
            })
        ref = self.clockify_all
        grouped_arrays = group_elements_by_key(ref, "id")

        for group in grouped_arrays:
            print(f"Group here {group}")
            if len(group) == 1:
                print(" \n \n Elemento unico ", group, flush=True)
                print("\n source ", group[0].get("source"))
                if group[0].get("source") == "api":
                    try:
                        create_clock_user(group[0])

                    except Exception as e:
                        print(f"An error occurred: {e}")

                else:
                    delete_clock_tag_by_id(group[0].get("id"))

            if len(group) == 2:
                ##Precisamos comparar os dois grupos
                if is_registers_divergents(group[0], group[1]):
                    try:
                        edit_tag(group[1].get("id"), group[1])
                    except Exception as e:
                        print(f"An error occurred: {e}")

        return {
            "message": "Clock user update done new",
            "all": self.clockify_all
        }
