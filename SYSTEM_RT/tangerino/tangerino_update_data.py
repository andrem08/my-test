import hashlib
import re
from datetime import date, datetime, timedelta

import pandas as pd
from dotenv import load_dotenv

from models import Current_worked_hours,  db

load_dotenv()


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def clean_cpf(cpf):
    return re.sub(r"\D", "", str(cpf))


def dataframe_to_dict_list(df):
    """Convert a DataFrame to a list of dictionaries."""
    return df.to_dict(orient="records")


def iterate_dict_list(dict_list):
    """Example function to iterate over the list of dictionaries."""
    for entry in dict_list:
        for key, value in entry.items():
            print(f"{key}: {value}")
        print("---")


class TangerinoUpdateData:
    def __init__(self, current_data):
        print("Updating tangerino time entries")
        self.df_tangerino = model_to_dataframe(Current_worked_hours)

