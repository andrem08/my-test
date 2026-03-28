import hashlib
import json
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

from models import (
    Client_by_CC,
    Clock_Time_Entry,
    Colaborador_cargo_value,
    Contexted_hour_entry,
    Indice_ano,
    PrimaData,
    Valor_base_by_cargo,
    db,
)
from utils.cost_center_manage import COST_CENTER_MANAGER

load_dotenv()


def extract_unique_values(array_of_dicts, key):
    unique_values = set()

    for dictionary in array_of_dicts:
        if key in dictionary:
            unique_values.add(dictionary[key])

    return list(unique_values)


def delete_contexted_hour_by_origem_id(id):
    entry_to_delete = (
        db.session.query(Contexted_hour_entry).filter_by(ORIGEM_ID=id).first()
    )

    if entry_to_delete:
        db.session.delete(entry_to_delete)
        db.session.commit()
        return True
    else:
        return False


def delete_prima_by_origem_id(id):
    entry_to_delete = db.session.query(PrimaData).filter_by(ID=id).first()

    if entry_to_delete:
        db.session.delete(entry_to_delete)
        db.session.commit()
        return True
    else:
        return False


def delete_clock_by_origem_id(id):
    entry_to_delete = db.session.query(Clock_Time_Entry).filter_by(id=id).first()

    if entry_to_delete:
        db.session.delete(entry_to_delete)
        db.session.commit()
        return True
    else:
        return False


def time_difference_in_minutes(datetime_str1, datetime_str2):
    difference = datetime_str1 - datetime_str2
    difference_in_minutes = difference.total_seconds() / 60
    return round(abs(difference_in_minutes))


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def generate_id_token(seed):
    hash_object = hashlib.sha256()
    hash_object.update(seed.encode("utf-8"))
    id_token = hash_object.hexdigest()

    return id_token


def verify_CC_by_id_ref(cc_ref):
    if cc_ref == "-1":
        cc_ref = "NO-SET"
    result = db.session.query(Client_by_CC).filter_by(CC=cc_ref).first()
    if result is None:
        return "NO-SET"
    return result.CC


def create_insertion_log(table, note):
    ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
    return ref


def all_origin_ids():
    all_ids = db.session.query(Contexted_hour_entry.ORIGEM_ID).all()
    all_ids = [row[0] for row in all_ids]

    return all_ids


def all_tokens():
    all_tokens = db.session.query(Contexted_hour_entry.TOKEN).all()
    all_tokens = [row[0] for row in all_tokens]

    return all_tokens


def group_elements_by_key(input_array, key):
    grouped_elements = {}
    for element in input_array:
        element_key = element.get(key)
        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []
            grouped_elements[element_key].append(element)
    return list(grouped_elements.values())


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            print(f"The key {key} are divergent", flush=True)
            print(f"ORIGINAL {reg_db[key]} -   NEW{reg_api[key]}", flush=True)
            return True
    return False


def query_models(model):
    return model.query.all()


def get_inner_array_sizes(array_of_arrays):
    sizes = []
    for inner_array in array_of_arrays:
        sizes.append(len(inner_array))
    return sizes


def get_inner_array_refs(array_of_arrays):
    refs = []
    for inner_array in array_of_arrays:
        elemet_ref = []
        for array_element in inner_array:
            elemet_ref.append(array_element.get("REF"))
        refs.append(elemet_ref)
    refs_sorted = sorted(refs, key=len)
    return refs_sorted


class ClockifyHourContexted:
    def __init__(self):
        load_dotenv()
        self.workspace_id = os.getenv("RT_CLOCKFY_WORKSPACE_ID")
        self.all_origem_ids = all_origin_ids()
        self.all_tokens = all_tokens()
        self.all_registers = query_models(Clock_Time_Entry)
        self.db_contexted_hours = query_models(Contexted_hour_entry)
        self.db_contexted_hours_prima = query_models(PrimaData)
        self.all = []
        self.insertion_logs = []
        self.error_logs = []
        self.local_regs = []
        self.local_prima_reg = []
        self.db_regs = []
        self.colaborador_cargo_df = model_to_dataframe(Colaborador_cargo_value)
        self.index_by_year_df = model_to_dataframe(Indice_ano)
        self.base_value_by_position_df = model_to_dataframe(Valor_base_by_cargo)
        self.CC_MANAGER = COST_CENTER_MANAGER()

    def create_insertion_log(self, table, note):
        ref = {"env": os.getenv("CONTEXT"), "table": table, "note": note}
        return ref

    def cargo_by_cargo_id(self, cargo_id):
        df = self.base_value_by_position_df
        result_df = df[df["id_local"] == cargo_id]
        if not result_df.empty:
            desired_value = result_df.iloc[0]["cargo"]
            return desired_value
        else:
            print("No matching rows found.")
            return -1

    def fator_by_year(self, ano):
        df = self.index_by_year_df
        result_df = df[df["id_ano"] == int(ano)]
        if not result_df.empty:
            desired_value = result_df.iloc[0]["indice"]
            return desired_value
        else:
            print("No matching rows found.")
            return -1

    def cargo_by_user(self, colaborador):
        df = self.colaborador_cargo_df
        result_df = df[df["colaborador"].str.lower() == colaborador.lower()]
        if not result_df.empty:
            desired_value = result_df.iloc[0]["cargo_id"]
            return desired_value
        else:
            print("No matching rows found.")
            return "-1"

    def hh_by_cargo(self, cargo):
        df = self.base_value_by_position_df
        result_df = df[df["id_local"] == cargo]
        if not result_df.empty:
            desired_value = result_df.iloc[0]["valor_base"]
            print(desired_value)
            return desired_value
        else:
            print("No matching rows found.")
            return -1

    def create_contexted_hours_reg_prima(self, register):
        timestamp_inicio = register.interval_start_moment
        timestamp_fim = register.interval_end_moment
        DATA_INICIO = timestamp_inicio.date().strftime("%d/%m/%Y")
        HORA_INICIO = timestamp_inicio.time().strftime("%H:%M")
        DATA_FINAL = timestamp_fim.date().strftime("%d/%m/%Y")
        HORA_FINAL = timestamp_fim.time().strftime("%H:%M")
        ANO = timestamp_inicio.date().strftime("%Y")
        USUARIO = register.USUARIO
        SEED = f"{DATA_INICIO}-{HORA_INICIO}-{DATA_FINAL}-{HORA_FINAL}-{USUARIO}"
        TOKEN = generate_id_token(SEED)
        CC_LABEL = register.CENTRO_DE_CUSTO
        ref = {
            "CC_LABEL": CC_LABEL,
            "CC_REF_ID": self.CC_MANAGER.verify_CC_by_id_ref(CC_LABEL),
            "PROJETO": register.PROJETO,
            "CLIENTE": register.CLIENTE,
            "DESCRICAO": register.DESCRICAO,
            "USUARIO": USUARIO,
            "GRUPO": "-1",
            "ATIVIDADE": register.ATIVIDADE,
            "DATA_INICIO": DATA_INICIO,
            "HORA_INICIO": HORA_INICIO,
            "DATA_FINAL": DATA_FINAL,
            "HORA_FINAL": HORA_FINAL,
            "HORAS_MINUTOS": time_difference_in_minutes(
                register.interval_start_moment, register.interval_end_moment
            ),
            "ANO": str(ANO),
            "ORIGEM": "PRIMA",
            "ORIGEM_ID": register.ID,
            "SEED": SEED,
            "TOKEN": TOKEN,
            "interval_start_moment": register.interval_start_moment,
            "interval_end_moment": register.interval_end_moment,
            "REF": "PRIMA",
        }
        self.local_prima_reg.append(ref)
        self.all.append(ref)

    def create_contexted_hour_reg(self, data_dict):
        print(" \n Registro a ser inserido", data_dict, flush=True)
        FATOR_ANO = float(self.fator_by_year(data_dict.get("ANO")))
        USUARIO = data_dict.get("USUARIO")
        cargo_of_user_id = self.cargo_by_user(USUARIO)
        cargo_of_user = self.cargo_by_cargo_id(cargo_of_user_id)
        HH_VALUE = float(self.hh_by_cargo(cargo_of_user_id))
        CC_LABEL = data_dict.get("CC_LABEL")
        CC_REF_ID = self.CC_MANAGER.verify_CC_by_id_ref(CC_LABEL)

        try:
            new_contexted_hour_entry = Contexted_hour_entry(
                CC_LABEL=CC_LABEL,
                CC_REF_ID=CC_REF_ID,
                PROJETO=data_dict.get("PROJETO"),
                CLIENTE=data_dict.get("CLIENTE"),
                DESCRICAO=data_dict.get("DESCRICAO"),
                USUARIO=USUARIO,
                GRUPO=data_dict.get("GRUPO"),
                ATIVIDADE=data_dict.get("ATIVIDADE"),
                DATA_INICIO=data_dict.get("DATA_INICIO"),
                HORA_INICIO=data_dict.get("HORA_INICIO"),
                DATA_FINAL=data_dict.get("DATA_FINAL"),
                HORA_FINAL=data_dict.get("HORA_FINAL"),
                HORAS_MINUTOS=data_dict.get("HORAS_MINUTOS"),
                HH=HH_VALUE,
                ANO=data_dict.get("ANO"),
                FATOR_ANO=FATOR_ANO,
                ORIGEM=data_dict.get("ORIGEM"),
                ORIGEM_ID=data_dict.get("ORIGEM_ID"),
                SEED=data_dict.get("SEED"),
                TOKEN=data_dict.get("TOKEN"),
                CARGO=cargo_of_user,
                interval_start_moment=data_dict.get("interval_start_moment"),
                interval_end_moment=data_dict.get("interval_end_moment"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.session.add(new_contexted_hour_entry)
            db.session.commit()
            print("Inserindo o registro new ", data_dict, flush=True)
            log = f"INSERTION OF {json.dumps(data_dict, default=str)}"
            self.insertion_logs.append(self.create_insertion_log("CONTEXTED_HOUR", log))
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            self.insertion_logs.append(
                self.create_insertion_log("CONTEXTED_HOUR", f"An error occurred: {e}")
            )

    def verify_register_token_is_new(self, token):
        if token in self.all_tokens:
            return False
        else:
            return True

    def format_local_contexted_hours(self, register):
        timestamp_inicio = register.interval_start_moment
        timestamp_fim = register.interval_end_moment
        DATA_INICIO = timestamp_inicio.date().strftime("%d/%m/%Y")
        HORA_INICIO = timestamp_inicio.time().strftime("%H:%M")
        DATA_FINAL = timestamp_fim.date().strftime("%d/%m/%Y")
        HORA_FINAL = timestamp_fim.time().strftime("%H:%M")
        ANO = timestamp_inicio.date().strftime("%Y")
        USUARIO = register.user.name
        SEED = f"{DATA_INICIO}-{HORA_INICIO}-{DATA_FINAL}-{HORA_FINAL}-{register.user.name}"
        TOKEN = generate_id_token(SEED)
        ref = {
            "CC_LABEL": register.project.cc_reference,
            "CC_REF_ID": self.CC_MANAGER.verify_CC_by_id_ref(
                register.project.cc_reference
            ),
            "PROJETO": register.project.name,
            "CLIENTE": register.project.client_name,
            "DESCRICAO": register.description,
            "USUARIO": USUARIO,
            "GRUPO": register.user.active_workspace,
            "ATIVIDADE": "",
            "DATA_INICIO": DATA_INICIO,
            "HORA_INICIO": HORA_INICIO,
            "DATA_FINAL": DATA_FINAL,
            "HORA_FINAL": HORA_FINAL,
            "HORAS_MINUTOS": time_difference_in_minutes(
                register.interval_start_moment, register.interval_end_moment
            ),
            "ANO": str(ANO),
            "ORIGEM": "CLOCK",
            "ORIGEM_ID": register.id,
            "SEED": SEED,
            "TOKEN": TOKEN,
            "interval_start_moment": register.interval_start_moment,
            "interval_end_moment": register.interval_end_moment,
            "REF": "CLOCK",
        }
        self.local_regs.append(ref)
        self.all.append(ref)

    def create_db_contexted_dict(self, register):
        ref = {
            "CC_LABEL": register.CC_LABEL,
            "CC_REF_ID": register.CC_REF_ID,
            "PROJETO": register.PROJETO,
            "CLIENTE": register.CLIENTE,
            "DESCRICAO": register.DESCRICAO,
            "USUARIO": register.USUARIO,
            "GRUPO": register.GRUPO,
            "ATIVIDADE": register.ATIVIDADE,
            "DATA_INICIO": register.DATA_INICIO,
            "HORA_INICIO": register.HORA_INICIO,
            "DATA_FINAL": register.DATA_FINAL,
            "HORA_FINAL": register.HORA_FINAL,
            "HORAS_MINUTOS": register.HORAS_MINUTOS,
            "ANO": str(register.ANO),
            "FATOR_ANO": register.FATOR_ANO,
            "HH": register.HH,
            "ORIGEM": register.ORIGEM,
            "ORIGEM_ID": register.ORIGEM_ID,
            "SEED": register.SEED,
            "TOKEN": register.TOKEN,
            "interval_start_moment": register.interval_start_moment,
            "interval_end_moment": register.interval_end_moment,
            "CARGO": register.CARGO,
            "REF": "DB",
        }
        self.all.append(ref)
        self.db_regs.append(ref)

    def query_dict_array(self, dict_array, key, value):
        return next((item for item in dict_array if item.get(key) == value), None)

    def verify_register_is_new(self, id):
        if id in self.all_origem_ids:
            return False
        else:
            print(f"Register {id} is new", flush=True)
            return True

    def verify_new_register(self, register):
        try:
            if self.verify_register_is_new(register.id):
                self.format_local_contexted_hours(register)
                self.create_contexted_hours(register)

        except Exception as e:
            print(f"An error occurred: {e}")

    async def format_hours(self, register):
        self.format_local_contexted_hours(register)

    async def create_db_contexted(self, db_register):
        self.create_db_contexted_dict(db_register)

    async def format_hours_reg_prima(self, prima_reg):
        self.create_contexted_hours_reg_prima(prima_reg)

    def get_element_by_id(self, id):
        return db.session.query(Contexted_hour_entry).filter_by(TOKEN=id).first()

    def edit_existing_element(self, id, data_dict, keys_to_update):
        existing_element = self.get_element_by_id(id)
        if existing_element is None:
            return None

        for key in keys_to_update:
            if key in data_dict:
                setattr(existing_element, key, data_dict[key])

        existing_element.updated_at = datetime.utcnow()
        db.session.commit()

        return existing_element

    def update_clock_hours(self):
        try:
            for db_register in self.db_contexted_hours:
                self.create_db_contexted_dict(db_register)
            for register in self.all_registers:
                self.format_local_contexted_hours(register)
            for prima_reg in self.db_contexted_hours_prima:
                self.create_contexted_hours_reg_prima(prima_reg)

            grouped_arrays = group_elements_by_key(self.all, "TOKEN")

            keys_ref = [
                "CC_LABEL",
                "CC_REF_ID",
                "PROJETO",
                "CLIENTE",
                "DESCRICAO",
                "USUARIO",
                "GRUPO",
                "ATIVIDADE",
                "DATA_INICIO",
                "HORA_INICIO",
                "DATA_FINAL",
                "HORA_FINAL",
                "HORAS_MINUTOS",
                "ANO",
            ]
            for group in grouped_arrays:
                size = len(group)
                if size == 1:
                    if group[0].get("REF") == "DB":
                        print("Registro  unico do db", flush=True)
                        print(f"\n \n Referencia aqui {group[0]}", flush=True)

                        if delete_contexted_hour_by_origem_id(
                            group[0].get("ORIGEM_ID")
                        ):
                            print(f" \n \n  Registro deletado {group[0]}", flush=True)

                    else:
                        token_ref = group[0].get("TOKEN")
                        id = group[0].get("ORIGEM_ID")
                        if self.verify_register_is_new(id):
                            print(
                                f"O registro é novo {group[0]} with id {id}", flush=True
                            )
                            if self.verify_register_token_is_new(token_ref):
                                self.create_contexted_hour_reg(group[0])

                        else:
                            print(
                                f"O registro não é novo {group[0]} with id {id}",
                                flush=True,
                            )
                            delete_contexted_hour_by_origem_id(id)
                            self.create_contexted_hour_reg(group[0])
                if size == 2:
                    reg_types = extract_unique_values(group, "REF")
                    if "DB" in reg_types:
                        if "PRIMA" in reg_types or "CLOCK" in reg_types:
                            if are_registers_divergent(group[0], group[1], keys_ref):
                                print("São divergentes mesmo", flush=True)
                                token_ref = group[0].get("TOKEN")
                                self.edit_existing_element(
                                    token_ref, group[1], keys_ref
                                )
                    if "PRIMA" in reg_types:
                        if "CLOCK" in reg_types:
                            print(
                                f" \n \n \n Aqui estão nossos casos quebrados  {group[0]}  -  {group[1]}\n \n ",
                                flush=True,
                            )
                if size > 2:
                    prima_refs = []
                    clock_refs = []
                    for reg in group:
                        print(f" \n reg {reg}", flush=True)

                        if reg.get("REF") == "PRIMA":
                            prima_refs.append(
                                {
                                    "REF": reg.get("REF"),
                                    "ORIGEM_ID": reg.get("ORIGEM_ID"),
                                }
                            )
                        if reg.get("REF") == "CLOCK":
                            clock_refs.append(
                                {
                                    "REF": reg.get("REF"),
                                    "ORIGEM_ID": reg.get("ORIGEM_ID"),
                                }
                            )
                    reg_types = extract_unique_values(group, "REF")
                    if "PRIMA" in reg_types and "CLOCK" in reg_types:
                        print("Aqui estamos")
                        for prima_ref in prima_refs:
                            print("Deletando lixo do prima", flush=True)
                            prima_id = prima_ref.get("ORIGEM_ID")
                            print(f"Deletando o registro com id {prima_id}", flush=True)
                            delete_prima_by_origem_id(prima_id)
                    else:
                        print(f" \n \n Clock data {reg_types}", flush=True)
                        print(f" \n prima refs {prima_refs}", flush=True)
                        print(f" \n clock refs  {clock_refs}", flush=True)
                        if prima_refs:
                            print("Deletando lixo do prima", flush=True)
                            prima_id = prima_refs[0].get("ORIGEM_ID")
                            print(f"Deletando o registro com id {prima_id}", flush=True)
                            delete_prima_by_origem_id(prima_id)
                        if clock_refs:
                            for clock_ref in clock_refs:
                                print("Deletando lixo do clock", flush=True)
                                clock_id = clock_ref.get("ORIGEM_ID")
                                print(
                                    f"Deletando o registro com id {clock_id}",
                                    flush=True,
                                )
                                delete_clock_by_origem_id(clock_id)

        except Exception as e:
            print("An error occurred while updating clock hours:", e, flush=True)

        return {
            "message": "Clock contexted hours updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
