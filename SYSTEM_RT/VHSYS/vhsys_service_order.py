import json
import os
import re
from datetime import datetime

import pandas as pd

from log_jobs.log_jobs import LogJobs
from models import CentroCustos, Client_by_CC, Extrato, ServiceOrder, db
from utils.api_to_json_manager import save_object_to_json_file
from utils.cost_center_manage import COST_CENTER_MANAGER
from utils.data_converter import model_to_dataframe
from VHSYS.api import api_results


def datetime_to_string(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_datetime(value):
    if isinstance(value, datetime):
        return value
    elif isinstance(value, str):
        if len(value) == 10:
            value += " 00:00:00"
        try:
            date_object = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return date_object
        except ValueError:
            raise ValueError(
                "The input value is not a valid datetime or string representation of a datetime."
            )
    elif value is None:
        return None
    else:
        raise ValueError(
            "The input value is not a valid datetime or string representation of a datetime."
        )


def is_valid_date_string(date_string):
    if date_string != "0000-00-00 00:00:00":
        return date_string
    return None


def extract_cc_value(input_string):
    pattern = re.compile(r"CC[-\s]*(\d+)|CC[-\s]*")
    match = pattern.search(input_string)

    if match and match.group(1):
        return int(match.group(1))
    else:
        return -1


def verify_numeric_float(number):
    try:
        if isinstance(number, str):
            number = number.strip()
            if number.isdigit():
                return int(number)
            else:
                return float(number)
        else:
            return float(number)
    except (ValueError, TypeError):
        return 0.0


def verify_numeric_int(number):
    if isinstance(number, int):
        return number
    if number.isdigit():
        return int(number)
    return 0.0


def verify_CC_by_id_ref(cc_ref):
    if cc_ref == "-1":
        cc_ref = "NO-SET"
    result = db.session.query(Client_by_CC).filter_by(CC=cc_ref).first()
    if result is None:
        return "NO-SET"
    return result.CC


def create_order(data):
    from utils.cost_center_manage import COST_CENTER_MANAGER

    cost_center_manager = COST_CENTER_MANAGER()
    ref_centro_custos = extract_cc_value(data["obs_interno_pedido"])
    new_service_order = ServiceOrder(
        nome_cliente=data["nome_cliente"],
        created_at=datetime.now(),
        data_cad_pedido=data["data_cad_pedido"],
        data_mod_pedido=is_valid_date_string(data["data_mod_pedido"]),
        data_pedido=is_valid_date_string(data["data_pedido"]),
        ref_centro_custos=ref_centro_custos,
        id_centro_custos=cost_center_manager.verify_CC_by_id_ref(
            str(ref_centro_custos)
        ),
        id_cliente=verify_numeric_int(data["id_cliente"]),
        id_ordem=verify_numeric_int(data["id_ordem"]),
        id_pedido=verify_numeric_int(data["id_pedido"]),
        lixeira=data["lixeira"],
        nota_servico_emitida=data["nota_servico_emitida"],
        obs_interno_pedido=data["obs_interno_pedido"],
        obs_pedido=data["obs_pedido"],
        referencia_ordem=data["referencia_ordem"],
        status_pedido=data["status_pedido"],
        tipo_servico=data["tipo_servico"],
        updated_at=datetime.now(),
        valor_total_desconto=float(data["valor_total_desconto"]),
        valor_total_despesas=float(data["valor_total_despesas"]),
        valor_total_pecas=float(data["valor_total_pecas"]),
        valor_total_os=float(data["valor_total_os"]),
        valor_total_servicos=float(data["valor_total_servicos"]),
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


def get_client_by_id(id):
    return db.session.query(ServiceOrder).filter_by(id_ordem=id).first()


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
            print(f"Types {type(reg_db[key])} - {type(reg_api[key])}")
            print(f"The key {key} are divergent", flush=True)
            print("DB reg", reg_db[key], flush=True)
            print("Api reg", reg_api[key], flush=True)

            return True
    return False


class VHSYS_SERVICE_ORDER:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/ordens-servico"
        self.new = []
        self.api_elements = []
        self.db_elements = []
        self.all = []
        self.insertion_logs = []
        self.error_logs = []
        self.registers_db = ServiceOrder.query.all()
        self.registers = api_results(self.url)
        self.CC_MANAGER = COST_CENTER_MANAGER()
        self.extracts_df = model_to_dataframe(Extrato)
        self.cc_df = model_to_dataframe(CentroCustos)

    @staticmethod
    def df_filter_to_dict_list(df: pd.DataFrame, column: str, value) -> list[dict]:
        filtered_df = df[df[column] == value]

        return filtered_df.to_dict(orient="records")

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def verify_valid_client_id_exist(self, client_id, cc_reference):
        if client_id != "0":
            return client_id
        else:
            print(f"CLIENTE ID DIVERGENTE {client_id} - {cc_reference}", flush=True)
            cc_table_reference = self.df_filter_to_dict_list(
                self.cc_df, "ref_centro_custos", str(cc_reference)
            )
            print(f"CC TABLE REFERECE {len(cc_table_reference)}")
            id_cc = cc_table_reference[0].get("id_centro_custos")
            print(f"Or id cc here {id_cc}", flush=True)
            filtered_extracts = self.extracts_df[self.extracts_df["id_cliente"] != 0]
            extract_table_reference = self.df_filter_to_dict_list(
                filtered_extracts, "id_centro_custos", str(id_cc)
            )
            # print(f" \n \n EXTRACT TABLE reference {extract_table_reference}", flush= True )
            if len(extract_table_reference) != 0:
                client_id_ref = extract_table_reference[0].get("id_cliente")
                print(f"Client id  here {client_id}", flush=True)
                return str(client_id_ref)
            return "0"

    def verify_elements(self):
        save_object_to_json_file(
            data=self.registers,
            filename="vhsys_OS_raw_api_data.json",
            directory="VHSYS/VHSYS_APIS_RESULTS",
        )
        print(" \n \n Validando os elementos \n \n")
        for register in self.registers:
            ref_cc = extract_cc_value(register["obs_interno_pedido"])
            register_dict = {
                "nome_cliente": register["nome_cliente"],
                "ref_centro_custos": ref_cc,
                "id_cliente": str(register["id_cliente"]),
                # "id_cliente": self.verify_valid_client_id_exist(str(register["id_cliente"]),ref_cc),
                "id_ordem": str(register["id_ordem"]),
                "id_pedido": str(register["id_pedido"]),
                "lixeira": register["lixeira"],
                "id_centro_custos": self.CC_MANAGER.verify_CC_by_id_ref(str(ref_cc)),
                "nota_servico_emitida": register["nota_servico_emitida"],
                "obs_interno_pedido": register["obs_interno_pedido"],
                "obs_pedido": register["obs_pedido"],
                "referencia_ordem": register["referencia_ordem"],
                "status_pedido": register["status_pedido"],
                "tipo_servico": register["tipo_servico"],
                "valor_total_desconto": verify_numeric_float(
                    register["valor_total_desconto"]
                ),
                "valor_total_despesas": verify_numeric_float(
                    register["valor_total_despesas"]
                ),
                "valor_total_pecas": verify_numeric_float(
                    register["valor_total_pecas"]
                ),
                "valor_total_os": verify_numeric_float(register["valor_total_os"]),
                "valor_total_servicos": verify_numeric_float(
                    register["valor_total_servicos"]
                ),
                "data_pedido": format_datetime(register["data_pedido"]),
                "data_cad_pedido": register["data_cad_pedido"],
                "data_mod_pedido": register["data_mod_pedido"],
                "source": "api",
            }

            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        for register in self.registers_db:
            register_dict = {
                "nome_cliente": register.nome_cliente,
                "ref_centro_custos": register.ref_centro_custos,
                "id_cliente": register.id_cliente,
                "id_ordem": register.id_ordem,
                "id_pedido": register.id_pedido,
                "lixeira": register.lixeira,
                "nota_servico_emitida": register.nota_servico_emitida,
                "obs_interno_pedido": register.obs_interno_pedido,
                "obs_pedido": register.obs_pedido,
                "referencia_ordem": register.referencia_ordem,
                "status_pedido": register.status_pedido,
                "tipo_servico": register.tipo_servico,
                "valor_total_desconto": register.valor_total_desconto,
                "valor_total_despesas": register.valor_total_despesas,
                "valor_total_pecas": register.valor_total_pecas,
                "valor_total_os": register.valor_total_os,
                "valor_total_servicos": register.valor_total_servicos,
                "id_centro_custos": register.id_centro_custos,
                "data_pedido": register.data_pedido,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "nome_cliente",
            "id_cliente",
            "id_ordem",
            "id_pedido",
            "lixeira",
            "nota_servico_emitida",
            "obs_interno_pedido",
            "obs_pedido",
            "referencia_ordem",
            "status_pedido",
            "tipo_servico",
            "valor_total_desconto",
            "valor_total_despesas",
            "valor_total_pecas",
            "valor_total_os",
            "valor_total_servicos",
            "id_centro_custos",
            "data_pedido",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_ordem")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        create_order(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")

            if len(group) == 2:
                if are_registers_divergent(group[1], group[0], keys_array):
                    try:
                        edit_existing_client(
                            group[0].get("id_ordem"), group[0], keys_array
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")

        return {
            "message": "Service order updated",
        }
