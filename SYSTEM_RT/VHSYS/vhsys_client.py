import json
import os
import re
from datetime import datetime

from log_jobs.log_jobs import LogJobs
from models import Client, db
from VHSYS.api import api_results


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


def create_client(data):
    print(f"Calling for create client {data}", flush=True)
    new_client = Client(
        id_cliente=verify_numeric_int(data["id_cliente"]),
        id_registro=verify_numeric_int(data["id_registro"]),
        tipo_cadastro=data["tipo_cadastro"],
        cnpj_cliente=data["cnpj_cliente"],
        razao_cliente=data["razao_cliente"],
        fantasia_cliente=data["fantasia_cliente"],
        endereco_cliente=data["endereco_cliente"],
        numero_cliente=data["numero_cliente"],
        bairro_cliente=data["bairro_cliente"],
        complemento_cliente=data["complemento_cliente"],
        referencia_cliente=data["referencia_cliente"],
        cep_cliente=data["cep_cliente"],
        cidade_cliente=data["cidade_cliente"],
        lixeira=data["lixeira"],
        uf_cliente=data["uf_cliente"],
        tel_destinatario_cliente=data["tel_destinatario_cliente"],
        doc_destinatario_cliente=data["doc_destinatario_cliente"],
        nome_destinatario_cliente=data["nome_destinatario_cliente"],
        email_cliente=data["email_cliente"],
        data_cad_cliente=data["data_cad_cliente"],
        data_mod_cliente=data["data_mod_cliente"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_client)
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


def get_client_by_id(id):
    return db.session.query(Client).filter_by(id_cliente=id).first()


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
            return True
    return False


class VHSYS_CLIENT:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/clientes"
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
        for register in registers:
            register_dict = {
                "id_cliente": str(verify_numeric_int(register["id_cliente"])),
                "id_registro": verify_numeric_int(register["id_registro"]),
                "tipo_cadastro": register["tipo_cadastro"],
                "cnpj_cliente": register["cnpj_cliente"],
                "razao_cliente": register["razao_cliente"],
                "fantasia_cliente": register["fantasia_cliente"],
                "endereco_cliente": register["endereco_cliente"],
                "numero_cliente": register["numero_cliente"],
                "bairro_cliente": register["bairro_cliente"],
                "complemento_cliente": register["complemento_cliente"],
                "referencia_cliente": register["referencia_cliente"],
                "cep_cliente": register["cep_cliente"],
                "lixeira": register["lixeira"],
                "cidade_cliente": register["cidade_cliente"],
                "uf_cliente": register["uf_cliente"],
                "tel_destinatario_cliente": register["tel_destinatario_cliente"],
                "doc_destinatario_cliente": register["doc_destinatario_cliente"],
                "nome_destinatario_cliente": register["nome_destinatario_cliente"],
                "email_cliente": register["email_cliente"],
                "data_cad_cliente": register["data_cad_cliente"],
                "data_mod_cliente": register["data_mod_cliente"],
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = Client.query.all()
        for register in registers_db:
            register_dict = {
                "id_cliente": register.id_cliente,
                "id_registro": register.id_registro,
                "tipo_cadastro": register.tipo_cadastro,
                "cnpj_cliente": register.cnpj_cliente,
                "razao_cliente": register.razao_cliente,
                "fantasia_cliente": register.fantasia_cliente,
                "endereco_cliente": register.endereco_cliente,
                "numero_cliente": register.numero_cliente,
                "bairro_cliente": register.bairro_cliente,
                "complemento_cliente": register.complemento_cliente,
                "referencia_cliente": register.referencia_cliente,
                "cep_cliente": register.cep_cliente,
                "cidade_cliente": register.cidade_cliente,
                "lixeira": register.lixeira,
                "uf_cliente": register.uf_cliente,
                "tel_destinatario_cliente": register.tel_destinatario_cliente,
                "doc_destinatario_cliente": register.doc_destinatario_cliente,
                "nome_destinatario_cliente": register.nome_destinatario_cliente,
                "email_cliente": register.email_cliente,
                "data_cad_cliente": register.data_cad_cliente,
                "data_mod_cliente": register.data_mod_cliente,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "id_cliente",
            "id_registro",
            "tipo_cadastro",
            "cnpj_cliente",
            "razao_cliente",
            "fantasia_cliente",
            "endereco_cliente",
            "numero_cliente",
            "bairro_cliente",
            "complemento_cliente",
            "referencia_cliente",
            "cep_cliente",
            "lixeira",
            "cidade_cliente",
            "uf_cliente",
            "tel_destinatario_cliente",
            "doc_destinatario_cliente",
            "email_cliente",
            "data_cad_cliente",
            "data_mod_cliente",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_cliente")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        log = f"INSERTION OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLIENT", log)
                        )
                        create_client(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.insertion_logs.append(
                            self.create_insertion_log(
                                "CLIENT", f"An error occurred: {e}"
                            )
                        )
            if len(group) == 2:
                if are_registers_divergent(group[0], group[1], keys_array):
                    try:
                        edit_existing_client(
                            group[0].get("id_cliente"), group[0], keys_array
                        )
                        log = f"EDIT  OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CLIENT", log)
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.insertion_logs.append(
                            self.create_insertion_log(
                                "CLIENT", f"An error occurred: {e}"
                            )
                        )
        log_jobs = LogJobs()
        log_jobs.post_insertion_update({"logs": self.insertion_logs})
        log_jobs.post_error_update({"logs": self.error_logs})
        return {
            "message": "Client register updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }

    def get_new_registers(self):
        return self.new
