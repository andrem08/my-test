import hashlib
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

from models import (
    Client_by_CC,
    Colaborador_cargo_value,
    Contexted_hour_entry,
    Indice_ano,
    PrimaData,
    Valor_base_by_cargo,
    db,
)

load_dotenv()


def cargo_by_cargo_id(cargo, df):
    print(f"Cargo here {cargo}", flush=True)
    result_df = df[df["id_local"] == cargo]
    if not result_df.empty:
        desired_value = result_df.iloc[0]["cargo"]
        print(f"Desire value {desired_value}", flush=True)
        print(desired_value)
        return desired_value
    else:
        print("No matching rows found.")
        return -1


def time_difference_in_minutes(datetime_str1, datetime_str2):
    difference = datetime_str1 - datetime_str2
    difference_in_minutes = difference.total_seconds() / 60
    return abs(difference_in_minutes)


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def fator_by_year(ano, df):
    result_df = df[df["id_ano"] == int(ano)]
    if not result_df.empty:
        desired_value = result_df.iloc[0]["indice"]
        print(desired_value)
        return desired_value
    else:
        print("No matching rows found.")
        return -1


def cargo_by_user(df, colaborador):
    result_df = df[df["colaborador"].str.lower() == colaborador.lower()]
    if not result_df.empty:
        desired_value = result_df.iloc[0]["cargo_id"]
        return desired_value
    else:
        print("No matching rows found.")
        return "-1"


def hh_by_cargo(cargo, df):
    result_df = df[df["id_local"] == cargo]
    if not result_df.empty:
        # Assuming you want to retrieve the 'desired_column' value from the first matching row
        desired_value = result_df.iloc[0]["valor_base"]
        print(desired_value)
        return desired_value
    else:
        print("No matching rows found.")
        return -1


def generate_id_token(seed):
    # Use hashlib to create a hash object
    hash_object = hashlib.sha256()

    # Update the hash object with the seed (string)
    hash_object.update(seed.encode("utf-8"))

    # Get the hexadecimal representation of the digest as the ID token
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


class PrimaHourContexted:
    def __init__(self):
        load_dotenv()
        self.workspace_id = os.getenv("RT_CLOCKFY_WORKSPACE_ID")
        self.all_origem_ids = all_origin_ids()
        self.all_tokens = all_tokens()
        self.all = []
        self.insertion_logs = []
        self.error_logs = []

    def query_db_clock_prima_entry(self):
        all_registers = PrimaData.query.all()
        for register in all_registers:
            self.verify_new_register(register)

    def create_contexted_hour_reg(self, data_dict):
        try:
            new_contexted_hour_entry = Contexted_hour_entry(
                CC_LABEL=data_dict.get("CC"),
                CC_REF_ID=data_dict.get("CC_REF_ID"),
                PROJETO=data_dict.get("PROJETO"),
                CLIENTE=data_dict.get("CLIENTE"),
                DESCRICAO=data_dict.get("DESCRICAO"),
                USUARIO=data_dict.get("USUARIO"),
                GRUPO=data_dict.get("GRUPO"),
                ATIVIDADE=data_dict.get("ATIVIDADE"),
                DATA_INICIO=data_dict.get("DATA_INICIO"),
                HORA_INICIO=data_dict.get("HORA_INICIO"),
                DATA_FINAL=data_dict.get("DATA_FINAL"),
                HORA_FINAL=data_dict.get("HORA_FINAL"),
                HORAS_MINUTOS=data_dict.get("HORAS_MINUTOS"),
                HH=data_dict.get("HH"),
                ANO=data_dict.get("ANO"),
                FATOR_ANO=data_dict.get("FATOR_ANO"),
                ORIGEM=data_dict.get("ORIGEM"),
                ORIGEM_ID=data_dict.get("ORIGEM_ID"),
                SEED=data_dict.get("SEED"),
                TOKEN=data_dict.get("TOKEN"),
                CARGO=data_dict.get("CARGO"),
                interval_start_moment=data_dict.get("interval_start_moment"),
                interval_end_moment=data_dict.get("interval_end_moment"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.session.add(new_contexted_hour_entry)
            db.session.commit()
            print("Inserindo o registro ", data_dict, flush=True)
            self.all.append(new_contexted_hour_entry)
            self.insertion_logs.append(
                create_insertion_log(
                    "PRIMA_HOUR", f" Insertion of {new_contexted_hour_entry}"
                )
            )
            return new_contexted_hour_entry

        except Exception as e:
            print(f"An error occurred: {str(e)}", flush=True)
            self.error_logs.append(
                create_insertion_log("PRIMA_HOUR", f"An error occurred: {e}")
            )

    def create_contexted_hours(self, register):
        print(f"Register from create context {register}", flush=True)
        colaborador_cargo_df = model_to_dataframe(Colaborador_cargo_value)
        index_by_year_df = model_to_dataframe(Indice_ano)
        base_value_by_position_df = model_to_dataframe(Valor_base_by_cargo)
        timestamp_inicio = register.interval_start_moment
        timestamp_fim = register.interval_end_moment
        DATA_INICIO = timestamp_inicio.date().strftime("%d/%m/%Y")
        HORA_INICIO = timestamp_inicio.time().strftime("%H:%M")
        DATA_FINAL = timestamp_fim.date().strftime("%d/%m/%Y")
        HORA_FINAL = timestamp_fim.time().strftime("%H:%M")
        ANO = timestamp_inicio.date().strftime("%Y")
        FATOR_ANO = fator_by_year(ANO, index_by_year_df)
        USUARIO = register.USUARIO
        print(f" \n \n USER {USUARIO}", flush=True)
        cargo_of_user_id = cargo_by_user(colaborador_cargo_df, USUARIO)
        cargo_of_user = cargo_by_cargo_id(cargo_of_user_id, base_value_by_position_df)
        print(f"Value of id {cargo_of_user_id }", flush=True)
        HH_VALUE = hh_by_cargo(cargo_of_user_id, base_value_by_position_df)
        SEED = f"{DATA_INICIO}-{HORA_INICIO}-{DATA_FINAL}-{HORA_FINAL}-{USUARIO}"
        TOKEN = generate_id_token(SEED)
        ref = {
            "CC": register.CENTRO_DE_CUSTO,
            "CC_REF_ID": verify_CC_by_id_ref(register.CENTRO_DE_CUSTO),
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
            "CATEGORIA": "-1",
            "ANO": ANO,
            "FATOR_ANO": FATOR_ANO,
            "HH": HH_VALUE,
            "ORIGEM": "PRIMA",
            "ORIGEM_ID": register.ID,
            "SEED": SEED,
            "TOKEN": TOKEN,
            "interval_start_moment": register.interval_start_moment,
            "interval_end_moment": register.interval_end_moment,
            "CARGO": cargo_of_user,
        }
        print(f"ref  contexted  {ref}", flush=True)
        if self.verify_register_token_is_new(TOKEN) is False:
            self.create_contexted_hour_reg(ref)

    def verify_register_is_new(self, id):
        if id in self.all_origem_ids:
            print(f"Register {id} alredy exist", flush=True)
            return True
        else:
            print(f"Register {id} is new", flush=True)
            return False

    def verify_register_token_is_new(self, token):
        if token in self.all_tokens:
            print(f"Register {token} alredy exist", flush=True)
            return True
        else:
            print(f"Register {token} is new", flush=True)
            return False

    def verify_new_register(self, register):
        try:
            if self.verify_register_is_new(register.ID) is False:
                self.create_contexted_hours(register)
        except Exception as e:
            print(f"An error occurred: {e}", flush=True)

    def update_prima_hours(self):
        try:
            self.query_db_clock_prima_entry()
        except Exception as e:
            print("An error occurred while updating clock hours:", e, flush=True)

        return {
            "message": "Prima hours updated",
            "logs": self.insertion_logs,
            "error": self.error_logs,
        }
