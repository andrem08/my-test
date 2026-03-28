import json
import os
import re
from datetime import datetime

from log_jobs.log_jobs import LogJobs
from models import Extrato, db
from VHSYS.api import api_results


def is_valid_date_string(date_string):
    if date_string != "0000-00-00 00:00:00":
        return date_string
    return None


def verify_numeric_float(number):
    if isinstance(number, float):
        return number
    return float(number)


def verify_numeric_int(number):
    if number is None:
        return -1
    if isinstance(number, int):
        return number
    return int(number)


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


def create_extract(data):
    new_service_order = Extrato(
        id_fluxo=verify_numeric_int(data["id_fluxo"]),
        id_banco=verify_numeric_int(data["id_banco"]),
        nome_conta=data["nome_conta"],
        id_cliente=verify_numeric_int(data["id_cliente"]),
        nome_cliente=data["nome_cliente"],
        data_fluxo=data["data_fluxo"],
        valor_fluxo=verify_numeric_float(data["valor_fluxo"]),
        observacoes_fluxo=data["observacoes_fluxo"],
        id_centro_custos=data["id_centro_custos"],
        centro_custos_fluxo=data["centro_custos_fluxo"],
        id_categoria=verify_numeric_int(data["id_categoria"]),
        categoria_fluxo=data["categoria_fluxo"],
        forma_pagamento=data["forma_pagamento"],
        tipo_fluxo=data["tipo_fluxo"],
        data_cad_fluxo=data["data_cad_fluxo"],
        data_mod_fluxo=data["data_mod_fluxo"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        lixeira=data["lixeira"],
    )
    db.session.add(new_service_order)
    db.session.commit()


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def get_element_by_id(id):
    return db.session.query(Extrato).filter_by(id_fluxo=id).first()


def edit_existing_element(id, data_dict, keys_to_update):
    existing_element = get_element_by_id(id)

    if existing_element is None:
        return None

    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_element, key, data_dict[key])

    existing_element.updated_at = datetime.utcnow()
    db.session.commit()

    return existing_element


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        ref_reg_db = reg_db[key]
        ref_reg_api = reg_api[key]
        if ref_reg_db != ref_reg_api:
            print(f"[{key}]  (db [{ref_reg_db}] local[{ref_reg_api}])")
            return True
    return False


class VHSYS_EXTRACT:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/extratos"
        self.new = []
        self.api_elements = []
        self.db_elements = []
        self.all = []
        self.insertion_logs = []
        self.error_logs = []

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def verify_elements(self):
        registers = api_results(self.url)
        print(f"\n \n \n VHSYS EXTRACT FROM API {registers}", flush = True),
        for register in registers:
            register_dict = {
                "id_fluxo": str(register["id_fluxo"]),
                "id_banco": verify_numeric_int(register["id_banco"]),
                "nome_conta": register["nome_conta"],
                "id_cliente": verify_numeric_int(register["id_cliente"]),
                "nome_cliente": register["nome_cliente"],
                "data_fluxo": register["data_fluxo"],
                "valor_fluxo": verify_numeric_float(register["valor_fluxo"]),
                "observacoes_fluxo": register["observacoes_fluxo"],
                "id_centro_custos": str(register["id_centro_custos"]),
                "centro_custos_fluxo": register["centro_custos_fluxo"],
                "id_categoria": verify_numeric_int(register["id_categoria"]),
                "categoria_fluxo": register["categoria_fluxo"],
                "forma_pagamento": register["forma_pagamento"],
                "tipo_fluxo": register["tipo_fluxo"],
                "data_cad_fluxo": register["data_cad_fluxo"],
                "data_mod_fluxo": register["data_mod_fluxo"],
                "lixeira": register["lixeira"],
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = Extrato.query.all()
        for register in registers_db:
            register_dict = {
                "id_fluxo": str(register.id_fluxo),
                "id_banco": register.id_banco,
                "nome_conta": register.nome_conta,
                "id_cliente": register.id_cliente,
                "nome_cliente": register.nome_cliente,
                "valor_fluxo": register.valor_fluxo,
                "observacoes_fluxo": register.observacoes_fluxo,
                "id_centro_custos": str(register.id_centro_custos),
                "centro_custos_fluxo": register.centro_custos_fluxo,
                "id_categoria": register.id_categoria,
                "categoria_fluxo": register.categoria_fluxo,
                "forma_pagamento": register.forma_pagamento,
                "tipo_fluxo": register.tipo_fluxo,
                "lixeira": register.lixeira,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "id_fluxo",
            "id_banco",
            "nome_conta",
            "id_cliente",
            "nome_cliente",
            "valor_fluxo",
            "observacoes_fluxo",
            "id_centro_custos",
            "centro_custos_fluxo",
            "id_categoria",
            "categoria_fluxo",
            "forma_pagamento",
            "lixeira",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_fluxo")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        log = f"INSERTION OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLIENT", log)
                        )
                        create_extract(group[0])
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
                        edit_existing_element(
                            group[0].get("id_fluxo"), group[0], keys_array
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
