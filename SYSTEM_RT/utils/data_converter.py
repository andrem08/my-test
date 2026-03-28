import logging
import pprint
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def to_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned_value = value.strip()
        if cleaned_value.endswith("."):
            cleaned_value = cleaned_value[:-1]
        try:
            return float(cleaned_value)
        except (ValueError, TypeError):
            return None

    logging.warning(
        f"Não foi possível converter o tipo {type(value)} com valor '{value}' para float."
    )
    return None


def to_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(float(value))
    except (ValueError, TypeError):
        logging.warning(f"Não foi possível converter '{value}' para int.")
        return None


def to_str(value):
    if value is None:
        return None
    return str(value).strip()


def model_to_dataframe(model):
    records = model.query.all()
    if not records:
        return pd.DataFrame()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column, None) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


class DataConverter:
    CONVERSION_MAP = {
        float: to_float,
        int: to_int,
        str: to_str,
    }

    def __init__(self, type_schema: dict):
        self.schema = type_schema

    def convert(self, data_dict: dict) -> dict:
        converted_data = {}
        for key, value in data_dict.items():
            target_type = self.schema.get(key)

            if target_type:
                converter_func = self.CONVERSION_MAP.get(target_type)
                if converter_func:
                    converted_data[key] = converter_func(value)
                else:
                    converted_data[key] = value
            else:
                converted_data[key] = value

        return converted_data
