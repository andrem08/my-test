import hashlib

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, jsonify

from clockfy.new_clockfy_hour_contexted import ClockifyHourContexted
from clockfy.prima_hour_contexted import PrimaHourContexted

load_dotenv()

contexted_hours_route = Blueprint("CONTEXTED_HOURS", __name__)


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def time_difference_in_minutes(datetime_str1, datetime_str2):
    return 0


def generate_id_token(seed):
    # Use hashlib to create a hash object
    hash_object = hashlib.sha256()

    # Update the hash object with the seed (string)
    hash_object.update(seed.encode("utf-8"))

    # Get the hexadecimal representation of the digest as the ID token
    id_token = hash_object.hexdigest()

    return id_token


@contexted_hours_route.route("/contexted_hours", methods=["PUT"])
def contexted_hours():
    # Extract column names from the model
    # Setar aqui as horas do clock
    clocky_hour_contexted = ClockifyHourContexted()
    # As horas do prima precisam ser inseridas previamente pela rota do bd_assets
    updates = clocky_hour_contexted.update_clock_hours()
    return jsonify(updates), 201


@contexted_hours_route.route("/contexted_hours_prima", methods=["PUT"])
def contexted_hours_prima():
    # Rora para setar os registros padrões do prima
    # Só precisa ser atualizado uma vez
    prima_hour_contexted = PrimaHourContexted()
    updates = prima_hour_contexted.update_prima_hours()
    return jsonify(updates), 201
