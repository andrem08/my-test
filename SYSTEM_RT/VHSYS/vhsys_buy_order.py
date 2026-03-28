import json
import os
import re
from datetime import datetime

from log_jobs.log_jobs import LogJobs
from models import Buy_order, db
from VHSYS.api import api_results


def convert_to_float(value):
    try:
        float_value = float(value)
        return float_value
    except ValueError:
        print(f"Error: Unable to convert {value} to float.")
        return None


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


def float_to_string_format(number, decimal_places=2):
    return format(number, f".{decimal_places}f")


def create_buy_order(data):
    new_buy_order = Buy_order(
        id_ordem=data["id_ordem"],
        id_pedido=data["id_pedido"],
        id_cliente=data["id_cliente"],
        nome_cliente=data["nome_cliente"],
        vendedor_pedido=data["vendedor_pedido"],
        valor_total_produtos=data["valor_total_produtos"],
        desconto_pedido=data["desconto_pedido"],
        peso_total_nota=data["peso_total_nota"],
        frete_pedido=data["frete_pedido"],
        valor_total_nota=data["valor_total_nota"],
        valor_baseICMS=data["valor_baseICMS"],
        valor_ICMS=data["valor_ICMS"],
        valor_baseST=data["valor_baseST"],
        valor_ST=data["valor_ST"],
        valor_IPI=data["valor_IPI"],
        condicao_pagamento_id=data["condicao_pagamento_id"],
        condicao_pagamento=data["condicao_pagamento"],
        transportadora_pedido=data["transportadora_pedido"],
        id_transportadora=data["id_transportadora"],
        data_pedido=data["data_pedido"],
        prazo_entrega=data["prazo_entrega"],
        obs_pedido=data["obs_pedido"],
        obs_interno_pedido=data["obs_interno_pedido"],
        status_pedido=data["status_pedido"],
        contas_pedido=data["contas_pedido"],
        estoque_pedido=data["estoque_pedido"],
        entrada_emitida=data["entrada_emitida"],
        usuario_cad_pedido=data["usuario_cad_pedido"],
        usuario_mod_pedido=data["usuario_mod_pedido"],
        data_cad_pedido=data["data_cad_pedido"],
        data_mod_pedido=data["data_mod_pedido"],
        lixeira=data["lixeira"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_buy_order)
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


def get_buy_order_by_id(id):
    return db.session.query(Buy_order).filter_by(id_ordem=id).first()


def edit_existing_buy_order(id_ordem, data_dict, keys_to_update):
    existing_buy_order = get_buy_order_by_id(id_ordem)

    if existing_buy_order is None:
        return None

    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_buy_order, key, data_dict[key])

    existing_buy_order.updated_at = datetime.utcnow()

    db.session.commit()

    return existing_buy_order


def compare_values(value1, value2):
    try:
        float_value1 = float(value1)
        float_value2 = float(value2)
        return float_value1 == float_value2
    except ValueError:
        try:
            date_format = "%Y-%m-%d"
            date_value1 = datetime.strptime(str(value1), date_format)
            date_value2 = datetime.strptime(str(value2), date_format)
            return date_value1 == date_value2
        except ValueError:
            return str(value1) == str(value2)


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        if compare_values(reg_db[key], reg_api[key]) is False:
            return True
    return False


class VHSYS_BUY_ORDER:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/ordens-compra"
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
                "id_ordem": register["id_ordem"],
                "id_pedido": register["id_pedido"],
                "id_cliente": register["id_cliente"],
                "nome_cliente": register["nome_cliente"],
                "vendedor_pedido": register["vendedor_pedido"],
                "valor_total_produtos": register["valor_total_produtos"],
                "desconto_pedido": register["desconto_pedido"],
                "peso_total_nota": register["peso_total_nota"],
                "frete_pedido": register["frete_pedido"],
                "valor_total_nota": register["valor_total_nota"],
                "valor_baseICMS": register["valor_baseICMS"],
                "valor_ICMS": register["valor_ICMS"],
                "valor_baseST": register["valor_baseST"],
                "valor_ST": register["valor_ST"],
                "valor_IPI": register["valor_IPI"],
                "condicao_pagamento_id": register["condicao_pagamento_id"],
                "condicao_pagamento": register["condicao_pagamento"],
                "transportadora_pedido": register["transportadora_pedido"],
                "id_transportadora": register["id_transportadora"],
                "data_pedido": register["data_pedido"],
                "prazo_entrega": register["prazo_entrega"],
                "obs_pedido": register["obs_pedido"],
                "obs_interno_pedido": register["obs_interno_pedido"],
                "status_pedido": register["status_pedido"],
                "contas_pedido": register["contas_pedido"],
                "estoque_pedido": register["estoque_pedido"],
                "entrada_emitida": register["entrada_emitida"],
                "usuario_cad_pedido": register["usuario_cad_pedido"],
                "usuario_mod_pedido": register["usuario_mod_pedido"],
                "data_cad_pedido": register["data_cad_pedido"],
                "data_mod_pedido": register["data_mod_pedido"],
                "lixeira": register["lixeira"],
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = Buy_order.query.all()
        for register in registers_db:
            register_dict = {
                "id_ordem": register.id_ordem,
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
                "condicao_pagamento_id": register.condicao_pagamento_id,
                "condicao_pagamento": register.condicao_pagamento,
                "transportadora_pedido": register.transportadora_pedido,
                "id_transportadora": register.id_transportadora,
                "data_pedido": register.data_pedido,
                "prazo_entrega": register.prazo_entrega,
                "obs_pedido": register.obs_pedido,
                "obs_interno_pedido": register.obs_interno_pedido,
                "status_pedido": register.status_pedido,
                "contas_pedido": register.contas_pedido,
                "estoque_pedido": register.estoque_pedido,
                "entrada_emitida": register.entrada_emitida,
                "usuario_cad_pedido": register.usuario_cad_pedido,
                "usuario_mod_pedido": register.usuario_mod_pedido,
                "data_cad_pedido": register.data_cad_pedido,
                "data_mod_pedido": register.data_mod_pedido,
                "lixeira": register.lixeira,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
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
            "condicao_pagamento_id",
            "condicao_pagamento",
            "transportadora_pedido",
            "id_transportadora",
            "data_pedido",
            "prazo_entrega",
            "obs_pedido",
            "obs_interno_pedido",
            "status_pedido",
            "contas_pedido",
            "estoque_pedido",
            "entrada_emitida",
            "lixeira",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_ordem")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        log = f"INSERTION OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("BUY_ORDER", log)
                        )
                        print(f" \n \n \n Creating buy order {group[0]} ", flush=True)
                        create_buy_order(group[0])
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
                        edit_existing_buy_order(
                            group[0].get("id_ordem"), group[0], keys_array
                        )
                        log = f"EDIT  OF {json.dumps(group[0])}"
                        self.insertion_logs.append(
                            self.create_insertion_log("BUY_ORDER", log)
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "BUY_ORDER", f"An error occurred: {e}"
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

    def get_new_registers(self):
        return self.new
