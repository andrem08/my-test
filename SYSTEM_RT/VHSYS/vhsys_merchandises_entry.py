import json
import os
import re
from datetime import datetime
from decimal import Decimal

from log_jobs.log_jobs import LogJobs
from models import Merch_entry, db
from VHSYS.api import api_results, api_results_parallel


def are_registers_divergent(reg_api, reg_db, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            return True
    return False


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def transform_and_save_dict_array_to_json(data_array, file_path):
    processed_data = []

    def _parse_and_handle_date(date_string):
        if not date_string:
            return None
        if date_string == "0000-00-00 00:00:00":
            return None
        try:
            # Handle ISO 8601 with or without 'Z'
            if isinstance(date_string, str):
                return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            return date_string  # If it's already a datetime object, return it as is
        except (ValueError, TypeError):
            print(
                f"Warning: Could not parse '{date_string}' as a valid date/time. Setting to None.",
                flush=True,
            )
            return None

    def _verify_numeric_float(number):
        if isinstance(number, (float, int)):
            return float(number)
        try:
            return float(number)
        except (ValueError, TypeError):
            return None

    def _verify_numeric_int(number):
        if number == "" or number is None:
            return -1
        try:
            return int(number)
        except (ValueError, TypeError):
            return -1

    for original_dict in data_array:
        transformed_dict = {}
        for key, value in original_dict.items():
            if "data_" in key or "created_at" in key or "updated_at" in key:
                transformed_dict[key] = _parse_and_handle_date(value)
            elif (
                "valor_" in key
                or "desconto_" in key
                or "peso_" in key
                or "frete_" in key
            ):
                transformed_dict[key] = _verify_numeric_float(value)
            elif "id_" in key and key not in [
                "id_entrada",
                "id_pedido",
                "id_cliente",
                "id_transportadora",
                "id_centro_custos",
            ]:
                transformed_dict[key] = _verify_numeric_int(value)
            else:
                transformed_dict[key] = value
        processed_data.append(transformed_dict)

    # Save the processed data to a JSON file
    with open(file_path, "w") as json_file:
        json.dump(
            processed_data, json_file, default=json_serializer, indent=4
        )  # Added indent for readability

    print(f"Data successfully transformed and saved to '{file_path}'")


def parse_iso_string(iso_string: str) -> datetime | None:
    if not iso_string:
        return None

    try:
        datetime_obj = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))

        return datetime_obj
    except (ValueError, TypeError):
        print(
            f"Warning: Could not parse '{iso_string}' as a valid date/time.", flush=True
        )
        return None


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


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


class VHSYS_MERCHANDISES_ENTRY:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/entradas-mercadoria"
        self.new = []
        self.api_elements = []
        self.db_elements = []
        self.all = []
        self.insertion_logs = []
        self.error_logs = []
        self.raw_api = []

    def create_vhsys_merchandises_entry(self, register):
        try:
            new_clock_time_entry = Merch_entry(
                id_entrada=register.get("id_entrada"),
                id_pedido=register.get("id_pedido"),
                id_cliente=register.get("id_cliente"),
                nome_cliente=register.get("nome_cliente"),
                vendedor_pedido=register.get("vendedor_pedido"),
                valor_total_produtos=register.get("valor_total_produtos"),
                desconto_pedido=register.get("desconto_pedido"),
                peso_total_nota=register.get("peso_total_nota"),
                frete_pedido=register.get("frete_pedido"),
                valor_total_nota=register.get("valor_total_nota"),
                valor_baseICMS=register.get("valor_baseICMS"),
                valor_ICMS=register.get("valor_ICMS"),
                valor_baseST=register.get("valor_baseST"),
                valor_ST=register.get("valor_ST"),
                valor_IPI=register.get("valor_IPI"),
                valor_PIS=register.get("valor_PIS"),
                valor_COFINS=register.get("valor_COFINS"),
                condicao_pagamento=register.get("condicao_pagamento"),
                transportadora_pedido=register.get("transportadora_pedido"),
                id_transportadora=register.get("id_transportadora"),
                data_pedido=register.get("data_pedido"),
                id_centro_custos=register.get("id_centro_custos"),
                centro_custos_pedido=register.get("centro_custos_pedido"),
                obs_pedido=register.get("obs_pedido"),
                obs_interno_pedido=register.get("obs_interno_pedido"),
                status_pedido=register.get("status_pedido"),
                contas_pedido=register.get("contas_pedido"),
                estoque_pedido=register.get("estoque_pedido"),
                nota_numero=register.get("nota_numero"),
                nota_chave=register.get("nota_chave"),
                nota_protocolo=register.get("nota_protocolo"),
                nota_data_autorizacao=register.get("nota_data_autorizacao"),
                data_cad_pedido=register.get("data_cad_pedido"),
                data_mod_pedido=register.get("data_mod_pedido"),
                modelo_nota=register.get("modelo_nota"),
                serie_nota=register.get("serie_nota"),
                importacao=register.get("importacao"),
                almoxarifado=register.get("almoxarifado"),
                lixeira=register.get("lixeira"),
                usuario_cad_pedido=register.get("usuario_cad_pedido"),
                usuario_mod_pedido=register.get("usuario_mod_pedido"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.session.add(new_clock_time_entry)
            db.session.commit()
            print("Inserindo o registro ", register, flush=True)
            return new_clock_time_entry
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def verify_elements_bd(self):
        registers_db = Merch_entry.query.all()
        for register in registers_db:
            register_dict = {
                "id_entrada": register.id_entrada,
                "id_pedido": register.id_pedido,
                "id_cliente": register.id_cliente,
                "nome_cliente": register.nome_cliente,
                "vendedor_pedido": register.vendedor_pedido,
                "valor_total_produtos": register.valor_total_produtos,
                "desconto_pedido": register.desconto_pedido,
                "peso_total_nota": register.peso_total_nota,
                "frete_pedido": register.frete_pedido,
                "valor_total_nota": register.valor_total_nota,
                "valor_baseICMS": register.valor_baseICMS,
                "valor_ICMS": register.valor_ICMS,
                "valor_baseST": register.valor_baseST,
                "valor_ST": register.valor_ST,
                "valor_IPI": register.valor_IPI,
                "valor_PIS": register.valor_PIS,
                "valor_COFINS": register.valor_COFINS,
                "condicao_pagamento": register.condicao_pagamento,
                "transportadora_pedido": register.transportadora_pedido,
                "id_transportadora": register.id_transportadora,
                "data_pedido": register.data_pedido,
                "id_centro_custos": register.id_centro_custos,
                "centro_custos_pedido": register.centro_custos_pedido,
                "obs_pedido": register.obs_pedido,
                "obs_interno_pedido": register.obs_interno_pedido,
                "status_pedido": register.status_pedido,
                "contas_pedido": register.contas_pedido,
                "estoque_pedido": register.estoque_pedido,
                "nota_numero": register.nota_numero,
                "nota_chave": register.nota_chave,
                "nota_protocolo": register.nota_protocolo,
                "nota_data_autorizacao": register.nota_data_autorizacao,
                "data_cad_pedido": register.data_cad_pedido,
                "data_mod_pedido": register.data_mod_pedido,
                "modelo_nota": register.modelo_nota,
                "serie_nota": register.serie_nota,
                "importacao": register.importacao,
                "almoxarifado": register.almoxarifado,
                "lixeira": register.lixeira,
                "usuario_cad_pedido": register.usuario_cad_pedido,
                "usuario_mod_pedido": register.usuario_mod_pedido,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements(self):
        registers = api_results(self.url)
        for register in registers:
            api_element = {
                "id_entrada": register["id_entrada"],
                "id_pedido": register["id_pedido"],
                "id_cliente": register["id_cliente"],
                "nome_cliente": register["nome_cliente"],
                "vendedor_pedido": register["vendedor_pedido"],
                "valor_total_produtos": verify_numeric_float(
                    register["valor_total_produtos"]
                ),
                "desconto_pedido": verify_numeric_float(register["desconto_pedido"]),
                "peso_total_nota": verify_numeric_float(register["peso_total_nota"]),
                "frete_pedido": verify_numeric_float(register["frete_pedido"]),
                "valor_total_nota": verify_numeric_float(register["valor_total_nota"]),
                "valor_baseICMS": verify_numeric_float(register["valor_baseICMS"]),
                "valor_ICMS": verify_numeric_float(register["valor_ICMS"]),
                "valor_baseST": verify_numeric_float(register["valor_baseST"]),
                "valor_ST": verify_numeric_float(register["valor_ST"]),
                "valor_IPI": verify_numeric_float(register["valor_IPI"]),
                "valor_PIS": verify_numeric_float(register["valor_PIS"]),
                "valor_COFINS": verify_numeric_float(register["valor_COFINS"]),
                "condicao_pagamento": register["condicao_pagamento"],
                "transportadora_pedido": register["transportadora_pedido"],
                "id_transportadora": register["id_transportadora"],
                "data_pedido": parse_iso_string(register["data_pedido"]),
                "id_centro_custos": register["id_centro_custos"],
                "centro_custos_pedido": register["centro_custos_pedido"],
                "obs_pedido": register["obs_pedido"],
                "obs_interno_pedido": register["obs_interno_pedido"],
                "status_pedido": register["status_pedido"],
                "contas_pedido": register["contas_pedido"],
                "estoque_pedido": register["estoque_pedido"],
                "nota_numero": register["nota_numero"],
                "nota_chave": register["nota_chave"],
                "nota_protocolo": register["nota_protocolo"],
                "nota_data_autorizacao": parse_iso_string(
                    register["nota_data_autorizacao"]
                ),
                "data_cad_pedido": parse_iso_string(register["data_cad_pedido"]),
                "data_mod_pedido": parse_iso_string(register["data_mod_pedido"]),
                "modelo_nota": register["modelo_nota"],
                "serie_nota": register["serie_nota"],
                "importacao": register["importacao"],
                "almoxarifado": register["almoxarifado"],
                "lixeira": register["lixeira"],
                "usuario_cad_pedido": register["usuario_cad_pedido"],
                "usuario_mod_pedido": register["usuario_mod_pedido"],
                "source": "api",
            }
            self.all.append(api_element)
            self.raw_api.append(register)
            self.api_elements.append(api_element)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "id_entrada",
            "id_pedido",
            "id_cliente",
            "nome_cliente",
            "vendedor_pedido",
            "valor_total_produtos",
            "desconto_pedido",
            "peso_total_nota",
            "frete_pedido",
            "valor_total_nota",
            "valor_baseICMS",
            "valor_ICMS",
            "valor_baseST",
            "valor_ST",
            "valor_IPI",
            "valor_PIS",
            "valor_COFINS",
            "condicao_pagamento",
            "transportadora_pedido",
            "id_transportadora",
            "data_pedido",
            "id_centro_custos",
            "centro_custos_pedido",
            "obs_pedido",
            "obs_interno_pedido",
            "status_pedido",
            "contas_pedido",
            "estoque_pedido",
            "nota_numero",
            "nota_chave",
            "nota_protocolo",
            "nota_data_autorizacao",
            "data_mod_pedido",
            "modelo_nota",
            "serie_nota",
            "importacao",
            "almoxarifado",
            "lixeira",
            "usuario_cad_pedido",
            "usuario_mod_pedido",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_entrada")

        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        print(f"Elemento { group[0]} sera criado")
                    except Exception as e:
                        print(f"An error occurred: {e}")

            if len(group) == 2:
                if are_registers_divergent(group[0], group[1], keys_array):
                    try:
                        print(f"Elemento { group[0]} sera editado")
                    except Exception as e:
                        print(f"An error occurred: {e}")

        return {
            "message": "Cost center register updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
