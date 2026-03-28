import json
import os
import re
from datetime import datetime
from utils.api_to_json_manager import save_object_to_json_file
from log_jobs.log_jobs import LogJobs
from models import ContaPagamento, db
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
    new_count_payment = ContaPagamento(
        id_conta_pag=data["id_conta_pag"],
        id_registro=data["id_registro"],
        nome_conta=data["nome_conta"],
        id_categoria=data["id_categoria"],
        categoria_pag=data["categoria_pag"],
        id_banco=data["id_banco"],
        id_fornecedor=data["id_fornecedor"],
        nome_fornecedor=data["nome_fornecedor"],
        vencimento_pag=data["vencimento_pag"],
        valor_pag=data["valor_pag"],
        valor_pago=data["valor_pago"],
        data_emissao=data["data_emissao"],
        n_documento_pag=data["n_documento_pag"],
        observacoes_pag=data["observacoes_pag"],
        id_centro_custos=data["id_centro_custos"],
        centro_custos_pag=data["centro_custos_pag"],
        liquidado_pag=data["liquidado_pag"],
        data_pagamento=data["data_pagamento"],
        obs_pagamento=data["obs_pagamento"],
        forma_pagamento=data["forma_pagamento"],
        valor_juros=data["valor_juros"],
        valor_desconto=data["valor_desconto"],
        valor_acrescimo=data["valor_acrescimo"],
        data_cad_pag=data["data_cad_pag"],
        data_mod_pag=data["data_mod_pag"],
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
    return db.session.query(ContaPagamento).filter_by(id_conta_pag=id).first()


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
        if value.startswith("0000-00-00") or value == "00/00/0000" or not value.strip():
            return None
        if len(value) == 10:
            value += " 00:00:00"
        try:
            date_object = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return date_object.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                date_object = datetime.strptime(value, "%d/%m/%Y %H:%M:%S")
                return date_object.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    elif value is not None:
        raise ValueError(
            "The input value is not a valid datetime or string representation of a datetime."
        )
    else:
        return None


def delete_conta_pag_by_id(id):
    entry_to_delete = (
        db.session.query(ContaPagamento).filter_by(id_conta_pag=id).first()
    )

    if entry_to_delete:
        db.session.delete(entry_to_delete)
        db.session.commit()
        return True
    else:
        return False


class VHSYS_CONTAS:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/contas-pagar"
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
            filename="vhsys_contas_a_pagar_raw_api_data.json",
            directory="VHSYS/VHSYS_APIS_RESULTS",
        )
        for register in registers:
            id_centro_custo = "-1"
            if str(register["id_centro_custos"]) != "0":
                id_centro_custo = str(register["id_centro_custos"])
            register_dict = {
                "id_conta_pag": str(register["id_conta_pag"]),
                "id_registro": register["id_registro"],
                "nome_conta": register["nome_conta"],
                "id_categoria": register["id_categoria"],
                "categoria_pag": register["categoria_pag"],
                "id_banco": register["id_banco"],
                "id_fornecedor": register["id_fornecedor"],
                "nome_fornecedor": register["nome_fornecedor"],
                "vencimento_pag": register["vencimento_pag"],
                "valor_pag": format_float(register["valor_pag"]),
                "valor_pago": format_float(register["valor_pago"]),
                "data_emissao": format_datetime(register["data_emissao"]),
                "n_documento_pag": register["n_documento_pag"],
                "observacoes_pag": register["observacoes_pag"],
                "id_centro_custos": id_centro_custo,
                "centro_custos_pag": register["centro_custos_pag"],
                "liquidado_pag": register["liquidado_pag"],
                "data_pagamento": format_datetime(register["data_pagamento"]),
                "obs_pagamento": register["obs_pagamento"],
                "forma_pagamento": register["forma_pagamento"],
                "valor_juros": format_float(register["valor_juros"]),
                "valor_desconto": format_float(register["valor_desconto"]),
                "valor_acrescimo": format_float(register["valor_acrescimo"]),
                "data_cad_pag": format_datetime(register["data_cad_pag"]),
                "data_mod_pag": format_datetime(register["data_mod_pag"]),
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
        registers_db = ContaPagamento.query.all()
        for register in registers_db:
            register_dict = {
                "id_conta_pag": register.id_conta_pag,
                "id_registro": register.id_registro,
                "nome_conta": register.nome_conta,
                "id_categoria": register.id_categoria,
                "categoria_pag": register.categoria_pag,
                "id_banco": register.id_banco,
                "id_fornecedor": register.id_fornecedor,
                "nome_fornecedor": register.nome_fornecedor,
                "vencimento_pag": register.vencimento_pag,
                "valor_pag": format_float(register.valor_pag),
                "valor_pago": format_float(register.valor_pago),
                "data_emissao": format_datetime(register.data_emissao),
                "n_documento_pag": register.n_documento_pag,
                "observacoes_pag": register.observacoes_pag,
                "id_centro_custos": str(register.id_centro_custos),
                "centro_custos_pag": register.centro_custos_pag,
                "liquidado_pag": register.liquidado_pag,
                "data_pagamento": format_datetime(register.data_pagamento),
                "obs_pagamento": register.obs_pagamento,
                "forma_pagamento": register.forma_pagamento,
                "valor_juros": format_float(register.valor_juros),
                "valor_desconto": format_float(register.valor_desconto),
                "valor_acrescimo": format_float(register.valor_acrescimo),
                "data_cad_pag": format_datetime(register.data_cad_pag),
                "data_mod_pag": format_datetime(register.data_mod_pag),
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
            "id_conta_pag",
            "id_registro",
            "nome_conta",
            "id_categoria",
            "categoria_pag",
            "id_banco",
            "id_fornecedor",
            "nome_fornecedor",
            "vencimento_pag",
            "valor_pag",
            "valor_pago",
            "data_emissao",
            "n_documento_pag",
            "observacoes_pag",
            "id_centro_custos",
            "centro_custos_pag",
            "liquidado_pag",
            "data_pagamento",
            "obs_pagamento",
            "forma_pagamento",
            "valor_juros",
            "valor_desconto",
            "valor_acrescimo",
            "data_cad_pag",
            "data_mod_pag",
            "agrupado",
            "agrupado_data",
            "agrupado_user",
            "agrupamento",
            "lixeira",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_conta_pag")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:

                        create_count_payment(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "CLIENT", f"An error occurred: {e}"
                            )
                        )
                if group[0].get("source") == "db":
                    try:
                        delete_conta_pag_by_id(group[0].get("id_conta_pag"))
                    except Exception as e:
                        print(f"An error occurred: {e}")

            if len(group) == 2:
                if are_registers_divergent(group[1], group[0], keys_array):
                    try:
                        edit_existing_conta(
                            group[0].get("id_conta_pag"), group[0], keys_array
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")

        return {
            "message": "vhsys register updated",
            "logs": self.insertion_logs,
        }

    def get_new_registers(self):
        return self.new
