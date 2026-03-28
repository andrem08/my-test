import hashlib
import os
import re
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import class_mapper

from log_jobs.log_jobs import LogJobs
from models import CentroCustos, OrdersManage, Pedido, ServiceOrder, db
from utils.api_to_json_manager import save_object_to_json_file
from utils.cost_center_manage import COST_CENTER_MANAGER


def verify_numeric_float(number):
    if number.isdigit():
        return float(number)
    return 0.0


def verify_numeric_int(number):
    if number.isdigit():
        return int(number)
    return 0.0


def get_objects_by_filters(model, filters):
    query = model.query
    if filters:
        query = query.filter_by(**filters)

    objects = query.all()
    objects_list = [model_to_dict(obj) for obj in objects]

    return objects_list


def model_to_dict(instance):
    return {
        column.key: getattr(instance, column.key)
        for column in class_mapper(instance.__class__).mapped_table.c
    }


def verify_keyword_divergence(line, first_keyword, second_keyord):
    if first_keyword in line:
        return line.get(first_keyword)
    if second_keyord in line:
        return line.get(second_keyord)
    return "-1"


def get_key_word_or_default(line, keyword, default):
    if keyword in line:
        reg = line.get(keyword)
        if reg == "":
            return None
        return reg
    return default


def get_origin_id(line):
    id_origem = get_key_word_or_default(line, "id_ordem", None)
    if id_origem is None:
        id_origem = get_key_word_or_default(line, "id_ped", None)
    return id_origem


def remove_non_int_values_for_key(array_of_dicts, target_key):
    for d in array_of_dicts:
        if target_key in d:
            value = d[target_key]
            if not isinstance(value, int):
                del d[target_key]


def group_dicts_by_key(input_array, key):
    result_dict = {}

    for d in input_array:
        if key in d:
            key_value = d[key]
            if key_value not in result_dict:
                result_dict[key_value] = []
            result_dict[key_value].append(d)

    result_array = list(result_dict.values())
    return result_array


def generate_id_token(seed):
    hash_object = hashlib.sha256()
    hash_object.update(seed.encode("utf-8"))
    id_token = hash_object.hexdigest()

    return id_token


def cc_to_date(date_str):
    if len(date_str) != 6:
        return None

    try:
        year = int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
    except ValueError:
        return None

    if year < 0 or month < 1 or month > 12 or day < 1 or day > 31:
        return None

    return datetime(year=2000 + year, month=month, day=day)


def create_orders_manage(cost_center_manager, data):
    ref_cc = data["ref_cc"]
    new_orders_manage = OrdersManage(
        ID=data["ID"],
        type=data["type"],
        id_origem=data["id_origem"],
        id_pedido=data["id_pedido"],
        id_cliente=data["id_cliente"],
        ref_cc=ref_cc,
        ref_date=cc_to_date(str(ref_cc)),
        id_cc_by_client=cost_center_manager.verify_CC_by_id_ref(str(ref_cc)),
        nome_cliente=data["nome_cliente"],
        vendedor_pedido=data["vendedor_pedido"],
        valor_total_produtos=data["valor_total_produtos"],
        desconto_pedido=data["desconto_pedido"],
        desconto_pedido_porc=data["desconto_pedido_porc"],
        peso_total_nota=data["peso_total_nota"],
        peso_total_nota_liq=data["peso_total_nota_liq"],
        frete_pedido=data["frete_pedido"],
        referencia_ordem=data["referencia_ordem"],
        valor_baseICMS=data["valor_baseICMS"],
        valor_ICMS=data["valor_ICMS"],
        valor_baseST=data["valor_baseST"],
        valor_ST=data["valor_ST"],
        valor_IPI=data["valor_IPI"],
        # condicao_pagamento_id=data["condicao_pagamento_id"],
        valor_total_servicos=data["valor_total_servicos"],
        valor_total_pecas=data["valor_total_pecas"],
        valor_total_despesas=data["valor_total_despesas"],
        valor_total_desconto=data["valor_total_desconto"],
        valor_total_os=data["valor_total_os"],
        frete_por_pedido=data["frete_por_pedido"],
        data_pedido=data["data_pedido"],
        prazo_entrega=data["prazo_entrega"],
        referencia_pedido=data["referencia_pedido"],
        obs_pedido=data["obs_pedido"],
        obs_interno_pedido=data["obs_interno_pedido"],
        status_pedido=data["status_pedido"],
        data_cad_pedido=data["data_cad_pedido"],
        data_mod_pedido=data["data_mod_pedido"],
        condicao_pagamento=data["condicao_pagamento"],
        valor_total_nota=data["valor_total_nota"],
        nota_servico_emitida=data["nota_servico_emitida"],
        lixeira=data["lixeira"],
        contas_pedido=data["contas_pedido"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(new_orders_manage)
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
    return db.session.query(OrdersManage).filter_by(ID=id).first()


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
            print(f"[{key}]  (db [{ref_reg_db}] local[{ref_reg_api}])", flush=True)
            return True
    return False


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def all_cost_center_refs():
    filter_condition = CentroCustos.lixeira == "Nao"
    all_refs = (
        db.session.query(CentroCustos.ref_centro_custos).filter(filter_condition).all()
    )
    all_refs = [row[0] for row in all_refs]
    return all_refs


class OrdersManager:
    def __init__(self):
        self.local_elements = []
        self.db_elements = []
        self.all = []
        self.insertion_logs = []
        self.error_logs = []
        self.cost_center_refs = all_cost_center_refs()

        # Requisitar o que monta aquele csv aqui
        self.cost_center_manager = COST_CENTER_MANAGER()
        self.cc_df = model_to_dataframe(CentroCustos)

    def hh_by_cargo(self, cargo):
        df = self.cc_df
        result_df = df[df["id_local"] == cargo]
        if not result_df.empty:
            desired_value = result_df.iloc[0]["valor_base"]
            print(desired_value)
            return desired_value
        else:
            print("No matching rows found.")
            return -1

    def verify_cc_exist(self, CC):
        print(f"Dentro da verificacao {CC}", flush=True)
        if CC == "-1":
            return False
        for cc_ref in self.cost_center_refs:
            if str(cc_ref) == str(CC):
                print(f" \n \n Temos aqui {cc_ref} {CC}", flush=True)
                return True

        return False

    def remove_os_words(self, text):
        if not isinstance(text, (str, bytes)):
            return ""
        pattern = r"\bOS[-\s]\w+\b"
        clean_text = re.sub(pattern, "", text)
        return clean_text

    def get_cc_reference(self, line):
        print(" \n  _______________________________________________", flush=True)
        ref_ordem = get_key_word_or_default(line, "id_pedido", None)
        label = self.cost_center_manager.get_cc_label(
            str(self.remove_os_words(ref_ordem))
        )
        if self.verify_cc_exist(label):
            return label
        ref_ordem = get_key_word_or_default(line, "referencia_ordem", None)
        label = self.cost_center_manager.get_cc_label(
            str(self.remove_os_words(ref_ordem))
        )
        if self.verify_cc_exist(label):
            return label
        ref_ordem = get_key_word_or_default(line, "referencia_pedido", None)
        label = self.cost_center_manager.get_cc_label(
            str(self.remove_os_words(ref_ordem))
        )
        if self.verify_cc_exist(label):
            print(f" \n \n Label from referencia_pedido {label}", flush=True)
            print(" \n  _______________________________________________", flush=True)
            return label
        print(f" \n \n Last Label {label}", flush=True)
        return "NO-SET"

    def process_value(self, value):
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return value

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def format_output(self, line, reference):
        id_origem = get_origin_id(line)
        seed = f"{reference}-{id_origem}"
        ID = generate_id_token(seed)
        id_pedido = get_key_word_or_default(line, "id_pedido", None)
        id_pedido_str = str(id_pedido)[:6]
        cc_ref = self.get_cc_reference(line)
        ref = {
            "ID": ID,
            "type": reference,
            "id_origem": id_origem,
            "ref_date": cc_to_date(str(id_pedido_str)),
            "id_cc_by_client": self.cost_center_manager.verify_CC_by_id_ref(
                str(cc_ref)
            ),
            "id_pedido": id_pedido,
            "id_cliente": get_key_word_or_default(line, "id_cliente", "-1"),
            "ref_cc": str(cc_ref),
            "nome_cliente": get_key_word_or_default(line, "nome_cliente", None),
            "vendedor_pedido": get_key_word_or_default(line, "vendedor_pedido", None),
            "valor_total_produtos": get_key_word_or_default(
                line, "valor_total_produtos", None
            ),
            "desconto_pedido": get_key_word_or_default(line, "desconto_pedido", None),
            "desconto_pedido_porc": get_key_word_or_default(
                line, "desconto_pedido_porc", None
            ),
            "peso_total_nota": get_key_word_or_default(line, "peso_total_nota", None),
            "peso_total_nota_liq": get_key_word_or_default(
                line, "peso_total_nota_liq", None
            ),
            "frete_pedido": get_key_word_or_default(line, "frete_pedido", None),
            "referencia_ordem": get_key_word_or_default(line, "referencia_ordem", None),
            "valor_baseICMS": get_key_word_or_default(line, "valor_baseICMS", None),
            "valor_ICMS": get_key_word_or_default(line, "valor_ICMS", None),
            "valor_baseST": get_key_word_or_default(line, "valor_baseST", None),
            "valor_ST": get_key_word_or_default(line, "valor_ST", None),
            "valor_IPI": get_key_word_or_default(line, "valor_IPI", None),
            "condicao_pagamento_id": get_key_word_or_default(
                line, "condicao_pagamento_id", None
            ),
            "condicao_pagamento": self.process_value(
                get_key_word_or_default(line, "condicao_pagamento", None)
            ),
            "valor_total_servicos": get_key_word_or_default(
                line, "valor_total_servicos", None
            ),
            "valor_total_pecas": get_key_word_or_default(
                line, "valor_total_pecas", None
            ),
            "valor_total_despesas": get_key_word_or_default(
                line, "valor_total_despesas", None
            ),
            "valor_total_desconto": get_key_word_or_default(
                line, "valor_total_desconto", None
            ),
            "valor_total_nota": get_key_word_or_default(line, "valor_total_nota", None),
            "nota_servico_emitida": get_key_word_or_default(
                line, "nota_servico_emitida", None
            ),
            "valor_total_os": get_key_word_or_default(line, "valor_total_os", None),
            "frete_por_pedido": get_key_word_or_default(line, "frete_por_pedido", None),
            "data_pedido": get_key_word_or_default(line, "data_pedido", None),
            "prazo_entrega": get_key_word_or_default(line, "prazo_entrega", None),
            "referencia_pedido": get_key_word_or_default(
                line, "referencia_pedido", None
            ),
            "obs_pedido": get_key_word_or_default(line, "obs_pedido", None),
            "obs_interno_pedido": get_key_word_or_default(
                line, "obs_interno_pedido", None
            ),
            "status_pedido": get_key_word_or_default(line, "status_pedido", None),
            "data_cad_pedido": get_key_word_or_default(line, "data_cad_pedido", None),
            "data_mod_pedido": get_key_word_or_default(line, "data_mod_pedido", None),
            "lixeira": get_key_word_or_default(line, "lixeira", None),
            "contas_pedido": get_key_word_or_default(line, "contas_pedido", None),
            "source": "local",
        }
        return ref

    def get_order_results(self):
        filter_pedidos = False
        filter_os = False
        filter_pedidos = False
        filter_os = False
        pedidos = get_objects_by_filters(Pedido, filter_pedidos)
        service_orders = get_objects_by_filters(ServiceOrder, filter_os)
        result = []

        for pedido in pedidos:
            ref_result = self.format_output(
                pedido,
                "OV",
            )
            result.append(ref_result)
            self.local_elements.append(ref_result)
            self.all.append(ref_result)
        for service_order in service_orders:
            ref_result = self.format_output(
                service_order,
                "OS",
            )
            result.append(ref_result)
            self.local_elements.append(ref_result)
            self.all.append(ref_result)
        remove_non_int_values_for_key(result, "centro_de_custo")
        return result

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def verify_elements_bd(self):
        registers_db = OrdersManage.query.all()
        for register in registers_db:
            ref = {
                "ID": register.ID,
                "type": register.type,
                "id_origem": register.id_origem,
                "id_pedido": register.id_pedido,
                "id_cliente": register.id_cliente,
                "ref_cc": register.ref_cc,
                "ref_date": register.ref_date,
                "id_cc_by_client": register.id_cc_by_client,
                "nome_cliente": register.nome_cliente,
                "vendedor_pedido": register.vendedor_pedido,
                "valor_total_produtos": register.valor_total_produtos,
                "desconto_pedido": register.desconto_pedido,
                "desconto_pedido_porc": register.desconto_pedido_porc,
                "peso_total_nota": register.peso_total_nota,
                "peso_total_nota_liq": register.peso_total_nota_liq,
                "frete_pedido": register.frete_pedido,
                "referencia_ordem": register.referencia_ordem,
                "valor_baseICMS": register.valor_baseICMS,
                "valor_ICMS": register.valor_ICMS,
                "valor_baseST": register.valor_baseST,
                "valor_ST": register.valor_ST,
                "valor_IPI": register.valor_IPI,
                "condicao_pagamento_id": register.condicao_pagamento_id,
                "valor_total_servicos": register.valor_total_servicos,
                "valor_total_pecas": register.valor_total_pecas,
                "valor_total_despesas": register.valor_total_despesas,
                "valor_total_desconto": register.valor_total_desconto,
                "valor_total_os": register.valor_total_os,
                "frete_por_pedido": register.frete_por_pedido,
                "data_pedido": register.data_pedido,
                "prazo_entrega": register.prazo_entrega,
                "referencia_pedido": register.referencia_pedido,
                "obs_pedido": register.obs_pedido,
                "obs_interno_pedido": register.obs_interno_pedido,
                "status_pedido": register.status_pedido,
                "data_cad_pedido": register.data_cad_pedido,
                "data_mod_pedido": register.data_mod_pedido,
                "condicao_pagamento": register.condicao_pagamento,
                "valor_total_nota": register.valor_total_nota,
                "nota_servico_emitida": register.nota_servico_emitida,
                "lixeira": register.lixeira,
                "contas_pedido": register.contas_pedido,
                "source": "db",
            }
            self.db_elements.append(ref)
            self.all.append(ref)

    def fix_datetime_serialization(objs):
        for obj in objs:
            for key, value in obj.items():
                if isinstance(value, datetime):
                    obj[key] = value.isoformat()

        return objs

    def get_updates(self):
        self.get_order_results()
        self.verify_elements_bd()
        grouped_arrays = group_elements_by_key(self.all, "ID")
        keys_array = [
            "type",
            "id_origem",
            "ref_cc",
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
            "referencia_ordem",
            "valor_baseICMS",
            "valor_ICMS",
            "valor_baseST",
            "valor_ST",
            "valor_IPI",
            "condicao_pagamento_id",
            "condicao_pagamento",
            "valor_total_nota",
            "nota_servico_emitida",
            "valor_total_servicos",
            "valor_total_pecas",
            "valor_total_despesas",
            "valor_total_desconto",
            "valor_total_os",
            "frete_por_pedido",
            "data_pedido",
            "prazo_entrega",
            "referencia_pedido",
            "obs_pedido",
            "obs_interno_pedido",
            "status_pedido",
            "data_cad_pedido",
            "data_mod_pedido",
            "lixeira",
            "contas_pedido",
            "ref_date",
            "id_cc_by_client",
        ]
        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "local":
                    lixeira = group[0].get("lixeira")
                    if lixeira == "Sim" or lixeira == "Nao":
                        try:
                            create_orders_manage(self.cost_center_manager, group[0])
                        except Exception as e:
                            print(f"An error occurred: {e}")
                            self.error_logs.append(
                                self.create_insertion_log(
                                    "ORDERS_MANAGER", f"An error occurred: {e}"
                                )
                            )

                else:
                    print(f" \n \n This register must be deleted {group[0]}")
            if len(group) == 2:
                if are_registers_divergent(group[1], group[0], keys_array):
                    try:
                        edit_existing_element(group[0].get("ID"), group[0], keys_array)

                    except Exception as e:
                        print(f"An error occurred: {e}")
                        self.error_logs.append(
                            self.create_insertion_log(
                                "ORDERS_MANAGER", f"An error occurred: {e}"
                            )
                        )
        log_jobs = LogJobs()

        return {
            "message": "Cost center register updated",
            # # "api": self.api_elements,
            # # "db": self.db_elements,
            # "logs": self.insertion_logs,
            # "error": self.error_logs,
            # "all": grouped_arrays,
        }
