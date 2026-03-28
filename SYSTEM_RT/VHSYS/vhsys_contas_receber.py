import json
import os
import re
from datetime import datetime
from utils.api_to_json_manager import save_object_to_json_file
from log_jobs.log_jobs import LogJobs
from models import ContaReceber, db
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


def create_count_payment(data):
    print(f"Calling for create account payment {data}", flush=True)
    new_count_payment = ContaReceber(
        id_conta_rec=data["id_conta_rec"],
        id_registro=data["id_registro"],
        nome_conta=data["nome_conta"],
        id_categoria=data["id_categoria"],
        categoria_rec=data["categoria_rec"],
        id_banco=data["id_banco"],
        id_cliente=data["id_cliente"],
        nome_cliente=data["nome_cliente"],
        vencimento_rec=data["vencimento_rec"],
        valor_rec=data["valor_rec"],
        valor_pago=data["valor_pago"],
        data_emissao=data["data_emissao"],
        n_documento_rec=data["n_documento_rec"],
        observacoes_rec=data["observacoes_rec"],
        centro_custos_rec=data["centro_custos_rec"],
        liquidado_rec=data["liquidado_rec"],
        data_pagamento=data["data_pagamento"],
        id_centro_custos=data["id_centro_custos"],
        obs_pagamento=data["obs_pagamento"],
        forma_pagamento=data["forma_pagamento"],
        valor_juros=data["valor_juros"],
        valor_desconto=data["valor_desconto"],
        valor_acrescimo=data["valor_acrescimo"],
        tipo_conta=data["tipo_conta"],
        data_cad_rec=data["data_cad_rec"],
        data_mod_rec=data["data_mod_rec"],
        agrupado=data["agrupado"],
        agrupado_data=data["agrupado_data"],
        agrupado_user=data["agrupado_user"],
        agrupamento=data["agrupamento"],
        lixeira=data["lixeira"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_count_payment)
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


def get_conta_by_id(id):
    return db.session.query(ContaReceber).filter_by(id_conta_rec=id).first()


def edit_existing_conta(id, data_dict, keys_to_update):
    existing_client = get_conta_by_id(id)

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
            ref_reg_db = reg_db[key]
            ref_reg_api = reg_api[key]
            print(
                f"(DIVERGENCES) DB {ref_reg_db} <-> API {ref_reg_api} ,({key}",
                flush=True,
            )
            return True
    return False


def format_float(value):
    if value is None:
        return format(0.0, ".2f")
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            raise ValueError(
                "The input value is not a valid float or string representation of a float."
            )

    if isinstance(value, float):
        return format(value, ".2f")
    else:
        raise ValueError(
            "The input value is not a valid float or string representation of a float."
        )


def format_datetime(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(value, str):
        if len(value) == 10:
            value += " 00:00:00"
        if value == "0000-00-00 00:00:00":
            return None
        try:
            date_object = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return date_object.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(
                "The input value is not a valid datetime or string representation of a datetime."
            )
    elif value is not None:
        raise ValueError(
            "The input value is not a valid datetime or string representation of a datetime."
        )
    else:
        return None


def delete_clock_hour_entry_by_id(id):
    entry_to_delete = db.session.query(ContaReceber).filter_by(id_conta_rec=id).first()

    if entry_to_delete:
        db.session.delete(entry_to_delete)
        db.session.commit()
        return True
    else:
        return False


class VHSYS_CONTAS_RECEBER:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/contas-receber"
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
            filename="vhsys_contas_a_receber_raw_api_data.json",
            directory="VHSYS/VHSYS_APIS_RESULTS",
        )
        for register in registers:
            id_centro_custo = "-1"
            if str(register["id_centro_custos"]) != "0":
                id_centro_custo = str(register["id_centro_custos"])
            register_dict = {
                "id_conta_rec": str(register["id_conta_rec"]),
                "id_registro": register["id_registro"],
                "nome_conta": register["nome_conta"],
                "id_categoria": register["id_categoria"],
                "categoria_rec": register["categoria_rec"],
                "id_banco": register["id_banco"],
                "id_cliente": register["id_cliente"],
                "nome_cliente": register["nome_cliente"],
                "vencimento_rec": format_datetime(register["vencimento_rec"]),
                "valor_rec": format_float(register["valor_rec"]),
                "valor_pago": format_float(register["valor_pago"]),
                "data_emissao": format_datetime(register["data_emissao"]),
                "n_documento_rec": register["n_documento_rec"],
                "observacoes_rec": register["observacoes_rec"],
                "id_centro_custos": id_centro_custo,
                "centro_custos_rec": register["centro_custos_rec"],
                "liquidado_rec": register["liquidado_rec"],
                "data_pagamento": format_datetime(register["data_pagamento"]),
                "obs_pagamento": register["obs_pagamento"],
                "forma_pagamento": register["forma_pagamento"],
                "valor_juros": format_float(register["valor_juros"]),
                "valor_desconto": format_float(register["valor_desconto"]),
                "valor_acrescimo": format_float(register["valor_acrescimo"]),
                "tipo_conta": str(register["tipo_conta"]),
                "data_cad_rec": format_datetime(register["data_cad_rec"]),
                "data_mod_rec": format_datetime(register["data_mod_rec"]),
                "agrupado": str(register["agrupado"]),
                "agrupado_data": format_datetime(register["agrupado_data"]),
                "agrupado_user": register["agrupado_user"],
                "agrupamento": str(register["agrupamento"]),
                "lixeira": register["lixeira"],
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = ContaReceber.query.all()
        for register in registers_db:
            id_centro_custo = "-1"
            if str(register.id_centro_custos) != "0":
                id_centro_custo = str(register.id_centro_custos)

            register_dict = {
                "id_conta_rec": str(register.id_conta_rec),
                "id_registro": register.id_registro,
                "nome_conta": register.nome_conta,
                "id_categoria": register.id_categoria,
                "categoria_rec": register.categoria_rec,
                "id_banco": register.id_banco,
                "id_cliente": register.id_cliente,
                "nome_cliente": register.nome_cliente,
                "vencimento_rec": format_datetime(register.vencimento_rec),
                "valor_rec": format_float(register.valor_rec),
                "valor_pago": format_float(register.valor_pago),
                "data_emissao": format_datetime(register.data_emissao),
                "n_documento_rec": register.n_documento_rec,
                "observacoes_rec": register.observacoes_rec,
                "centro_custos_rec": register.centro_custos_rec,
                "liquidado_rec": register.liquidado_rec,
                "data_pagamento": format_datetime(register.data_pagamento),
                "id_centro_custos": id_centro_custo,
                "obs_pagamento": register.obs_pagamento,
                "forma_pagamento": register.forma_pagamento,
                "valor_juros": format_float(register.valor_juros),
                "valor_desconto": format_float(register.valor_desconto),
                "valor_acrescimo": format_float(register.valor_acrescimo),
                "tipo_conta": str(register.tipo_conta),
                "data_cad_rec": format_datetime(register.data_cad_rec),
                "data_mod_rec": format_datetime(register.data_mod_rec),
                "agrupado": str(register.agrupado),
                "agrupado_data": format_datetime(register.agrupado_data),
                "agrupado_user": register.agrupado_user,
                "agrupamento": str(register.agrupamento),
                "lixeira": register.lixeira,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "id_conta_rec",
            "id_registro",
            "nome_conta",
            "id_categoria",
            "categoria_rec",
            "id_banco",
            "id_cliente",
            "nome_cliente",
            "vencimento_rec",
            "valor_rec",
            "valor_pago",
            "data_emissao",
            "n_documento_rec",
            "observacoes_rec",
            "centro_custos_rec",
            "liquidado_rec",
            "data_pagamento",
            "id_centro_custos",
            "obs_pagamento",
            "forma_pagamento",
            "valor_juros",
            "valor_desconto",
            "valor_acrescimo",
            "tipo_conta",
            "data_cad_rec",
            "data_mod_rec",
            "agrupado",
            "agrupado_data",
            "agrupado_user",
            "agrupamento",
            "lixeira",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_conta_rec")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        log = f"INSERTION OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CONTAS_RECEBER", log)
                        )
                        create_count_payment(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "CONTAS_RECEBER", f"An error occurred: {e}"
                            )
                        )
                if group[0].get("source") == "db":
                    ref_id = group[0].get("id_conta_rec")
                    print(f"Vamos deletar nossos registro {ref_id} aqui", flush=True)
                    delete_clock_hour_entry_by_id(ref_id)

            if len(group) == 2:
                if are_registers_divergent(group[0], group[1], keys_array):
                    try:
                        edit_existing_conta(
                            group[0].get("id_conta_rec"), group[0], keys_array
                        )
                        log = f"EDIT  OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("CONTAS_RECEBER", log)
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "CONTAS_RECEBER", f"An error occurred: {e}"
                            )
                        )
        log_jobs = LogJobs()
        log_jobs.post_insertion_update({"logs": self.insertion_logs})
        log_jobs.post_error_update({"logs": self.error_logs})
        return {
            "message": "Cost center register updated",
            "api": self.api_elements,
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }

    def get_new_registers(self):
        return self.new
