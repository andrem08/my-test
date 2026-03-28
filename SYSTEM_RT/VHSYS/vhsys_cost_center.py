import json
import os
import re
from datetime import datetime

import pandas as pd

from log_jobs.log_jobs import LogJobs
from models import CentroCustos, Client_by_CC, db
from utils.cost_center_manage import COST_CENTER_MANAGER
from VHSYS.api import api_results


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def verify_numeric_float(number):
    if number.isdigit():
        return float(number)
    return 0.0


def verify_numeric_int(number):
    if isinstance(number, int):
        return number
    if number.isdigit():
        return int(number)
    return 0.0


def status_centro_custo(status):
    if status == "Ativo":
        return True
    return False


def status_lixeira(status):
    if status == "Sim":
        return True
    return False


def extract_numeric_part(text):
    pattern = re.compile(r"\b(\d{6})\b")
    match = pattern.search(text)

    if match:
        return int(match.group(1))
    else:
        return -1


def extract_prefix(text):
    pattern = r"^[A-Z]{2}-[A-Z0-9]{3}"
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    else:
        return -1


def get_cc_label(text):
    if text == "Vendas":
        return text
    if text == "Administração":
        return text
    label = extract_numeric_part(text)
    if label == -1:
        label = extract_prefix(text)
        return label
    return label


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def get_client_by_id(id):
    return db.session.query(CentroCustos).filter_by(id_centro_custos=id).first()


def edit_existing_client(user_id, data_dict, keys_to_update):
    existing_client = get_client_by_id(user_id)

    if existing_client is None:
        return None

    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_client, key, data_dict[key])

    existing_client.updated_at = datetime.utcnow()

    db.session.commit()

    return existing_client


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            print(f"The key {key} are divergent", flush=True)
            print("DB reg", reg_db[key], flush=True)
            print("Api reg", reg_api[key], flush=True)
            return True
    return False


def verify_CC_by_id_ref(cc_ref):
    if cc_ref == "-1":
        cc_ref = "NO-SET"
    result = db.session.query(Client_by_CC).filter_by(CC=cc_ref).first()
    if result is None:
        return "NO-SET"
    return result.CC


class VHSYS_COST_CENTER:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/centros-custo"
        self.new = []
        self.api_elements = []
        self.db_elements = []
        self.all = []
        self.insertion_logs = []
        self.error_logs = []
        self.df_client_by_cc = model_to_dataframe(Client_by_CC)

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def client_by_cc(self, cc):
        df = self.df_client_by_cc
        result_df = df[df["CC"].astype(str).str.strip() == cc.strip()]
        if not result_df.empty:
            desired_value = result_df.iloc[0]["CLIENT"]
            print(desired_value)
            return desired_value
        else:
            print("No matching rows found.")
            return "-1"

    def create_cost_center(self, data):
        ref_centro_custos = get_cc_label(data["desc_centro_custos"])
        new_centro = CentroCustos(
            id_centro_custos=data["id_centro_custos"],
            desc_centro_custos=data["desc_centro_custos"],
            status_centro_custos=data["status_centro_custos"],
            data_cad_centro=data["data_cad_centro"],
            lixeira=data["lixeira"],
            ref_centro_custos=ref_centro_custos,
        )

        db.session.add(new_centro)
        db.session.commit()

    def define_client(self, cc):
        if cc == "-1":
            print("ADM CLIENT")
            return "RT_ENG"
        client = self.client_by_cc(cc)
        return client

    def verify_elements(self):
        CC_MANAGER = COST_CENTER_MANAGER()
        registers = api_results(self.url)
        for register in registers:
            register_dict = {
                "id_centro_custos": str(register["id_centro_custos"]),
                "desc_centro_custos": register["desc_centro_custos"],
                "status_centro_custos": register["status_centro_custos"],
                "data_cad_centro": register["data_cad_centro"],
                "lixeira": register["lixeira"],
                "ref_centro_custos": str(
                    CC_MANAGER.get_cc_label(register["desc_centro_custos"])
                ),
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = CentroCustos.query.all()
        for register in registers_db:
            register_dict = {
                "id_centro_custos": register.id_centro_custos,
                "desc_centro_custos": register.desc_centro_custos,
                "status_centro_custos": register.status_centro_custos,
                "data_cad_centro": register.data_cad_centro,
                "lixeira": register.lixeira,
                "ref_centro_custos": register.ref_centro_custos,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "desc_centro_custos",
            "status_centro_custos",
            "lixeira",
            "ref_centro_custos",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_centro_custos")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        log = f"INSERTION OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLIENT", log)
                        )
                        self.create_cost_center(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "CLIENT", f"An error occurred: {e}"
                            )
                        )
            if len(group) == 2:
                if are_registers_divergent(group[0], group[1], keys_array):
                    try:
                        edit_existing_client(
                            group[0].get("id_centro_custos"), group[0], keys_array
                        )
                        log = f"EDIT  OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLIENT", log)
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "CLIENT", f"An error occurred: {e}"
                            )
                        )
        log_jobs = LogJobs()
        log_jobs.post_insertion_update({"logs": self.insertion_logs})
        log_jobs.post_error_update({"logs": self.error_logs})
        return {
            "message": "Cost center register updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
