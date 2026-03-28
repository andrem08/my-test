import json
import os
import re
from datetime import datetime

from log_jobs.log_jobs import LogJobs
from models import Banks, db
from utils.api_to_json_manager import save_object_to_json_file
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
    if number == "":
        return -1
    if not number:
        return -1
    if number is None:
        return -1
    try:
        number_as_int = int(number)
        return number_as_int
    except (ValueError, TypeError):
        return -1


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


def format_float(value):
    if value is None:
        return format(0.0, ".2f")
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            # trunk-ignore(ruff/B904)
            raise ValueError(
                "The input value is not a valid float or string representation of a float."
            )

    if isinstance(value, float):
        return format(value, ".2f")
    else:
        raise ValueError(
            "The input value is not a valid float or string representation of a float."
        )


def create_bank(data):
    new_bank = Banks(
        id_banco_cad=data["id_banco_cad"],
        nome_banco_cad=data["nome_banco_cad"],
        # saldo_inicial=data["saldo_inicial"],
        # saldo_inicial_data=data["saldo_inicial_data"],
        id_carteira=data["id_carteira"],
        carteira_banco=verify_numeric_int(data["carteira_banco"]),
        convenio_banco=verify_numeric_int(data["convenio_banco"]),
        cedente_banco=verify_numeric_int(data["cedente_banco"]),
        agencia_banco=verify_numeric_int(data["agencia_banco"]),
        conta_banco=verify_numeric_int(data["conta_banco"]),
        codigo_cedente=verify_numeric_int(data["codigo_cedente"]),
        status_banco=data["status_banco"],
        com_registro=data["com_registro"],
        data_cad_banco=data["data_cad_banco"],
        data_mod_banco=data["data_mod_banco"],
        lixeira=data["lixeira"],
        numero_banco=str(data["numero_banco"]),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(new_bank)
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
    return db.session.query(Banks).filter_by(id_banco_cad=id).first()


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
        if reg_db[key] != reg_api[key]:
            ref_reg_db = reg_db[key]
            ref_reg_api = reg_api[key]
            print(
                f"(DIVERGENCES) DB {ref_reg_db} <-> API {ref_reg_api} ,({key}",
                flush=True,
            )
            return True
    return False


class VHSYS_BANKS:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/contas-bancarias"
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
        save_object_to_json_file(
            data=registers,
            filename="vhsys_banks_raw_api_data.json",
            directory="VHSYS/VHSYS_APIS_RESULTS",
        )
        for register in registers:
            print(f" \n \n Register {register}", flush=True)
            register_dict = {
                "id_banco_cad": register["id_banco_cad"],
                "nome_banco_cad": register["nome_banco_cad"],
                # "saldo_inicial": format_float(register["saldo_inicial"]),
                # "saldo_inicial_data": register["saldo_inicial_data"],
                "id_carteira": verify_numeric_int(register["id_carteira"]),
                "carteira_banco": verify_numeric_int(register["carteira_banco"]),
                "convenio_banco": verify_numeric_int(register["convenio_banco"]),
                "cedente_banco": verify_numeric_int(register["cedente_banco"]),
                "agencia_banco": verify_numeric_int(register["agencia_banco"]),
                "conta_banco": verify_numeric_int(register["conta_banco"]),
                "codigo_cedente": verify_numeric_int(register["codigo_cedente"]),
                "status_banco": register["status_banco"],
                "com_registro": register["com_registro"],
                "data_cad_banco": register["data_cad_banco"],
                "data_mod_banco": register["data_mod_banco"],
                "lixeira": register["lixeira"],
                "numero_banco": str(register["numero_banco"]),
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = Banks.query.all()
        for register in registers_db:
            register_dict = {
                "id_banco_cad": register.id_banco_cad,
                "nome_banco_cad": register.nome_banco_cad,
                # "saldo_inicial": format_float(register.saldo_inicial),
                # "saldo_inicial_data": register.saldo_inicial_data,
                "id_carteira": verify_numeric_int(register.id_carteira),
                "carteira_banco": register.carteira_banco,
                "convenio_banco": verify_numeric_int(register.convenio_banco),
                "cedente_banco": verify_numeric_int(register.cedente_banco),
                "agencia_banco": verify_numeric_int(register.agencia_banco),
                "conta_banco": verify_numeric_int(register.conta_banco),
                "codigo_cedente": verify_numeric_int(register.codigo_cedente),
                "status_banco": register.status_banco,
                "com_registro": register.com_registro,
                "data_cad_banco": register.data_cad_banco,
                "data_mod_banco": register.data_mod_banco,
                "lixeira": register.lixeira,
                "numero_banco": str(register.numero_banco),
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "nome_banco_cad",
            # "saldo_inicial",
            "id_carteira",
            "carteira_banco",
            "convenio_banco",
            "cedente_banco",
            "agencia_banco",
            "conta_banco",
            "codigo_cedente",
            "status_banco",
            "com_registro",
            "lixeira",
            "numero_banco",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_banco_cad")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        log = f"INSERTION OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLIENT", log)
                        )
                        create_bank(group[0])
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
                            group[0].get("id_banco_cad"), group[0], keys_array
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
            "message": "banks register updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
