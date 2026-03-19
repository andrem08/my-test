import json
import os
from datetime import datetime

from models import DespesasRecorrentes, db
from update_extension_manager import UPDATE_EXTENSION_STATUS


def transform_to_datetime(date_string):
    if date_string is None:
        return None

    if len(date_string) == 10:
        # If the length is 10, it contains only date information
        return datetime.strptime(date_string, "%Y-%m-%d")
    elif len(date_string) == 19:
        # If the length is 19, it contains both date and time information
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    else:
        # If the length is neither 10 nor 19, raise an error
        raise ValueError("Invalid date format")


def create_regular_bill(data):
    new_regular_bills = DespesasRecorrentes(
        id_custo=data["id_custo"],
        id_empresa=data["id_empresa"],
        nome_conta=data["nome_conta"],
        id_categoria=data["id_categoria"],
        categoria_custo=data["categoria_custo"],
        id_banco=data["id_banco"],
        id_fornecedor=data["id_fornecedor"],
        nome_fornecedor=data["nome_fornecedor"],
        vencimento_custo=data["vencimento_custo"],
        valor_custo=data["valor_custo"],
        observacoes_custo=data["observacoes_custo"],
        id_centro_custos=data["id_centro_custos"],
        status_custo=data["status_custo"],
        forma_pagamento=data["forma_pagamento"],
        periodicidade=data["periodicidade"],
        dia_semana_ocorrencia=data["dia_semana_ocorrencia"],
        dia_mes_ocorrencia=data["dia_mes_ocorrencia"],
        intervalo_dias_ocorrencia=data["intervalo_dias_ocorrencia"],
        data_inicio_ocorrencia=data["data_inicio_ocorrencia"],
        data_fim_ocorrencia=data["data_fim_ocorrencia"],
        data_cad_custo=data["data_cad_custo"],
        lixeira=data["lixeira"],
        # created_at=datetime.now(),
        # updated_at=datetime.now(),
    )
    # print(f" \n \n Creating regular bills of data : {data}")
    db.session.add(new_regular_bills)
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
    return db.session.query(DespesasRecorrentes).filter_by(id_custo=id).first()


def edit_existing_element(id, data_dict, keys_to_update):
    existing_element = get_element_by_id(id)

    # If the user doesn't exist, you might want to handle that case accordingly
    if existing_element is None:
        # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
        return None

    # Update the instance based on keys_to_update
    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_element, key, data_dict[key])

    # Update the 'updated_at' property
    existing_element.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.session.commit()

    return existing_element


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            ref_reg_db = reg_db[key]
            ref_reg_api = reg_api[key]
            print(
                f"(DIVERGENCES) DB {ref_reg_db} <-> API {ref_reg_api} ,({key})",
                flush=True,
            )
            return True
    return False


def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def save_to_json(data, file_path):
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, default=datetime_serializer)


class REGULAR_BILLS_MANAGE:
    def __init__(self, data):
        self.new = []
        self.api_source = data
        self.api_elements = []
        self.db_elements = []
        self.all = []
        self.update_report_status = UPDATE_EXTENSION_STATUS("REGULAR_BILLS")
        self.update_report_status.update_run_status(1)
        print("Runnig regualr bills manager")

        # print(f"API SOURCE DATA {self.api_source}")

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def verify_elements(self):
        registers = self.api_source
        # print(f"\n \n \n Registers {registers}", flush=True)

        for register in registers:
            data_inicio_ocorrencia = register["data_inicio_ocorrencia"]
            data_fim_ocorrencia = register["data_fim_ocorrencia"]
            data_cad_custo = register["data_cad_custo"]
            f_data_inicio_ocorrencia = f"{data_inicio_ocorrencia}T00:00:00"
            f_data_fim_ocorrencia = f"{data_fim_ocorrencia}T00:00:00"
            f_data_cad_custo = f"{data_cad_custo}T00:00:00"
            register_dict = {
                "id_custo": str(register["id_custo"]),
                "id_empresa": str(register["id_empresa"]),
                "nome_conta": register["nome_conta"],
                "id_categoria": str(register["id_categoria"]),
                "categoria_custo": register["categoria_custo"],
                "id_banco": str(register["id_banco"]),
                "id_fornecedor": str(register["id_fornecedor"]),
                "nome_fornecedor": register["nome_fornecedor"],
                "vencimento_custo": str(register["vencimento_custo"]),
                "valor_custo": str(register["valor_custo"]),
                "observacoes_custo": register["observacoes_custo"],
                "id_centro_custos": str(register["id_centro_custos"]),
                "status_custo": register["status_custo"],
                "forma_pagamento": register["forma_pagamento"],
                "periodicidade": str(register["periodicidade"]),
                "dia_semana_ocorrencia": str(register["dia_semana_ocorrencia"]),
                "dia_mes_ocorrencia": str(register["dia_mes_ocorrencia"]),
                "intervalo_dias_ocorrencia": register["intervalo_dias_ocorrencia"],
                "data_inicio_ocorrencia": transform_to_datetime(data_inicio_ocorrencia),
                "data_fim_ocorrencia": transform_to_datetime(data_fim_ocorrencia),
                "data_cad_custo": transform_to_datetime(data_cad_custo),
                "lixeira": register["lixeira"],
                "source": "api",
            }
            # print(f" \n \n Register dict {register_dict}", flush=True)
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = DespesasRecorrentes.query.all()
        for register in registers_db:
            register_dict = {
                "id_custo": register.id_custo,
                "id_empresa": register.id_empresa,
                "nome_conta": register.nome_conta,
                "id_categoria": register.id_categoria,
                "categoria_custo": register.categoria_custo,
                "id_banco": register.id_banco,
                "id_fornecedor": register.id_fornecedor,
                "nome_fornecedor": register.nome_fornecedor,
                "vencimento_custo": register.vencimento_custo,
                "valor_custo": register.valor_custo,
                "observacoes_custo": register.observacoes_custo,
                "id_centro_custos": register.id_centro_custos,
                "status_custo": register.status_custo,
                "forma_pagamento": register.forma_pagamento,
                "periodicidade": register.periodicidade,
                "dia_semana_ocorrencia": str(register.dia_semana_ocorrencia),
                "dia_mes_ocorrencia": register.dia_mes_ocorrencia,
                "intervalo_dias_ocorrencia": register.intervalo_dias_ocorrencia,
                "data_inicio_ocorrencia": register.data_inicio_ocorrencia,
                "data_fim_ocorrencia": register.data_fim_ocorrencia,
                "data_cad_custo": register.data_cad_custo,
                "lixeira": register.lixeira,
                "source": "db",
            }
            # print(f" \n \n Register db {register_dict}", flush=True)
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "id_custo",
            "id_empresa",
            "nome_conta",
            "id_categoria",
            "categoria_custo",
            "id_banco",
            "id_fornecedor",
            "nome_fornecedor",
            "vencimento_custo",
            "valor_custo",
            "observacoes_custo",
            "id_centro_custos",
            "status_custo",
            "forma_pagamento",
            "periodicidade",
            "dia_semana_ocorrencia",
            "dia_mes_ocorrencia",
            "intervalo_dias_ocorrencia",
            "data_inicio_ocorrencia",
            "data_fim_ocorrencia",
            "data_cad_custo",
            "lixeira",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_custo")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        create_regular_bill(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.update_report_status = UPDATE_EXTENSION_STATUS(
                            "REGULAR_BILLS"
                        )
                        self.update_report_status.update_run_status(-1)
            if len(group) == 2:
                if are_registers_divergent(group[0], group[1], keys_array):
                    try:
                        edit_existing_element(
                            group[0].get("id_custo"), group[0], keys_array
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.update_report_status = UPDATE_EXTENSION_STATUS(
                            "REGULAR_BILLS"
                        )
                        self.update_report_status.update_run_status(-1)

        self.update_report_status = UPDATE_EXTENSION_STATUS("REGULAR_BILLS")
        self.update_report_status.update_run_status(2)
        return {
            "message": "Regular Bills registers updated",
        }
