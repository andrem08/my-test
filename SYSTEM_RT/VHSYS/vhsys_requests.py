import json
import os
from datetime import datetime

from models import Pedido, db
from utils.api_to_json_manager import save_object_to_json_file
from utils.cost_center_manage import COST_CENTER_MANAGER
from VHSYS.api import api_results


def convert_date_format(input_date):
    try:
        parsed_date = datetime.strptime(input_date, "%d/%m/%Y")

        # Add a default time and time zone
        default_time = datetime.strptime("00:00:00", "%H:%M:%S").time()
        default_datetime = datetime.combine(parsed_date, default_time)

        return default_datetime
    except ValueError:
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


def format_datetime(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(value, str):
        if len(value) == 10:
            value += " 00:00:00"
        try:
            date_object = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return date_object.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            # trunk-ignore(ruff/B904)
            raise ValueError(
                "The input value is not a valid datetime or string representation of a datetime."
            )
    elif value is not None:
        raise ValueError(
            "The input value is not a valid datetime or string representation of a datetime."
        )
    else:
        return None


def create_request(data):
    new_pedido = Pedido(
        id_ped=str(verify_numeric_int(data["id_ped"])),
        id_pedido=str(verify_numeric_int(data["id_pedido"])),
        id_cliente=str(verify_numeric_int(data["id_cliente"])),
        nome_cliente=data["nome_cliente"],
        cc=data["cc"],
        id_cc=data["id_cc"],
        vendedor_pedido=data["vendedor_pedido"],
        valor_total_produtos=data["valor_total_produtos"],
        desconto_pedido=data["desconto_pedido"],
        desconto_pedido_porc=data["desconto_pedido_porc"],
        peso_total_nota=data["peso_total_nota"],
        peso_total_nota_liq=data["peso_total_nota_liq"],
        frete_pedido=data["frete_pedido"],
        valor_total_nota=data["valor_total_nota"],
        valor_baseICMS=data["valor_baseICMS"],
        valor_ICMS=data["valor_ICMS"],
        valor_baseST=data["valor_baseST"],
        valor_ST=data["valor_ST"],
        valor_IPI=data["valor_IPI"],
        condicao_pagamento=data["condicao_pagamento"],
        frete_por_pedido=data["frete_por_pedido"],
        data_pedido=data["data_pedido"],
        prazo_entrega=verify_numeric_int(data["prazo_entrega"]),
        referencia_pedido=data["referencia_pedido"],
        obs_pedido=data["obs_pedido"],
        obs_interno_pedido=data["obs_interno_pedido"],
        status_pedido=data["status_pedido"],
        data_cad_pedido=data["data_cad_pedido"],
        data_mod_pedido=data["data_mod_pedido"],
        lixeira=data["lixeira"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_pedido)
    db.session.commit()


def convert_string_to_datetime(date_string):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


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
    return db.session.query(Pedido).filter_by(id_ped=id).first()


def edit_existing_element(id, data_dict, keys_to_update):
    existing_element = get_element_by_id(id)
    print(f"Data that will be edited {data_dict}", flush=True)

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
        ref_reg_db = reg_db.get(key)
        ref_reg_api = reg_api.get(key)
        if ref_reg_db != ref_reg_api:
            print(
                f"\n \n OR KEY IS DIVERGENT {key} [ {ref_reg_db} - {ref_reg_api}] \n \n "
            )
            print(f"\n \n REG API {reg_api}", flush = True)
            print(f"\n \n REG DB {reg_db}", flush = True)
            return True
    return False


class VHSYS_REQUESTS:
    def __init__(self):
        self.url = "https://api.vhsys.com/v2/pedidos"
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
            filename="vhsys_request_raw_api_data.json",
            directory="VHSYS/VHSYS_APIS_RESULTS",
        )
        CC_MANAGER = COST_CENTER_MANAGER()
        print(f"API WITHOUT FORMAT REGISTERS {len(registers)}")
        for register in registers:
            cc = str(CC_MANAGER.get_cc_label(register["referencia_pedido"]))
            if cc == "-1":
                cc = str(CC_MANAGER.get_cc_label(register["obs_interno_pedido"]))
            register_dict = {
                "id_ped": str(register["id_ped"]),
                "id_pedido": str(register["id_pedido"]),
                "id_cliente": str(register["id_cliente"]),
                "nome_cliente": register["nome_cliente"],
                "cc": cc,
                "id_cc": CC_MANAGER.verify_CC_by_id_ref(cc),
                "vendedor_pedido": register["vendedor_pedido"],
                "valor_total_produtos": format_float(register["valor_total_produtos"]),
                "desconto_pedido": format_float(register["desconto_pedido"]),
                "desconto_pedido_porc": format_float(register["desconto_pedido_porc"]),
                "peso_total_nota": format_float(register["peso_total_nota"]),
                "peso_total_nota_liq": format_float(register["peso_total_nota_liq"]),
                "frete_pedido": format_float(register["frete_pedido"]),
                "valor_total_nota": format_float(register["valor_total_nota"]),
                "valor_baseICMS": format_float(register["valor_baseICMS"]),
                "valor_ICMS": format_float(register["valor_ICMS"]),
                "valor_baseST": format_float(register["valor_baseST"]),
                "valor_ST": format_float(register["valor_ST"]),
                "valor_IPI": format_float(register["valor_IPI"]),
                # "condicao_pagamento_id": str(register["condicao_pagamento_id"]),
                "condicao_pagamento": str(register["condicao_pagamento"]),
                "frete_por_pedido": register["frete_por_pedido"],
                "prazo_entrega": register["prazo_entrega"],
                "referencia_pedido": register["referencia_pedido"],
                "obs_pedido": register["obs_pedido"],
                "obs_interno_pedido": register["obs_interno_pedido"],
                "status_pedido": register["status_pedido"],
                "data_pedido": register["data_pedido"],
                "data_cad_pedido": convert_string_to_datetime(register["data_cad_pedido"]),
                "data_mod_pedido": convert_string_to_datetime(register["data_mod_pedido"]),
                "lixeira": register["lixeira"],
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = Pedido.query.all()
        CC_MANAGER = COST_CENTER_MANAGER()
        for register in registers_db:
            cc = str(CC_MANAGER.get_cc_label(register.referencia_pedido))
            if cc == "-1":
                cc = str(CC_MANAGER.get_cc_label(register.obs_interno_pedido))
            register_dict = {
                "id_ped": str(register.id_ped),
                "id_pedido": str(register.id_pedido),
                "id_cliente": str(register.id_cliente),
                "nome_cliente": register.nome_cliente,
                "vendedor_pedido": register.vendedor_pedido,
                "valor_total_produtos": format_float(register.valor_total_produtos),
                "desconto_pedido": format_float(register.desconto_pedido),
                "cc": cc,
                "id_cc": CC_MANAGER.verify_CC_by_id_ref(cc),
                "desconto_pedido_porc": format_float(register.desconto_pedido_porc),
                "peso_total_nota": format_float(register.peso_total_nota),
                "peso_total_nota_liq": format_float(register.peso_total_nota_liq),
                "frete_pedido": format_float(register.frete_pedido),
                "valor_total_nota": format_float(register.valor_total_nota),
                "valor_baseICMS": format_float(register.valor_baseICMS),
                "valor_ICMS": format_float(register.valor_ICMS),
                "valor_baseST": format_float(register.valor_baseST),
                "valor_ST": format_float(register.valor_ST),
                "valor_IPI": format_float(register.valor_IPI),
                # "condicao_pagamento_id": str(register.condicao_pagamento_id),
                "condicao_pagamento": str(register.condicao_pagamento),
                "frete_por_pedido": register.frete_por_pedido,
                "prazo_entrega": register.prazo_entrega,
                "referencia_pedido": register.referencia_pedido,
                "obs_pedido": register.obs_pedido,
                "obs_interno_pedido": register.obs_interno_pedido,
                "status_pedido": register.status_pedido,
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
        print(f"\n \n \n Exibindo elementos da api  {len(self.api_elements)} \n \n \n")
        keys_array = [
            "id_pedido",
            "id_cliente",
            "nome_cliente",
            "vendedor_pedido",
            "valor_total_produtos",
            "desconto_pedido",
            "desconto_pedido_porc",
            "peso_total_nota",
            "peso_total_nota_liq",
            "frete_pedido",
            "valor_total_nota",
            "valor_baseICMS",
            "valor_ICMS",
            "valor_baseST",
            "valor_ST",
            "valor_IPI",
            "condicao_pagamento_id",
            "condicao_pagamento",
            "frete_por_pedido",
            "cc",
            "id_cc",
            "referencia_pedido",
            "obs_pedido",
            "obs_interno_pedido",
            "status_pedido",
            "lixeira",
        ]
        grouped_arrays = group_elements_by_key(self.all, "id_ped")
        print(f"\n \n \n Grouped arrays size {len(grouped_arrays)} \n \n ")
        count = 0
        print(f"Init count size {len(grouped_arrays)}")
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    print(f"Single api register {group[0]}")
                    try:
                        # log = f"INSERTION OF {json.dumps(group[0])}"
                        # self.insertion_logs.append(
                        #     self.create_insertion_log("CLIENT", log)
                        # )
                        print(f"\n \n Try to create request for {group[0]} \n \n")
                        create_request(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        # self.error_logs.append(
                        #     self.create_insertion_log(
                        #         "CLIENT", f"An error occurred: {e}"
                        #     )
                        # )
                else:
                    print(f"Only in db register,must be delete {group[0]}")
            if len(group) == 2:
                print(f" \n Count value {count}")
                count += 1
                if are_registers_divergent(group[1], group[0], keys_array):
                    try:
                        edit_existing_element(
                            group[0].get("id_ped"), group[0], keys_array
                        )
                        #log = f"EDIT  OF {json.dumps(group[1])}"
                        # self.insertion_logs.append(
                        #     self.create_insertion_log("PEDIDO", log)
                        # )
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        #self.error_logs.append(
                         #   self.create_insertion_log(
                          #      "CLIENT", f"An error occurred: {e}"
                          #  )
                        #)
        return {
            "message": "Request updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
  
        }