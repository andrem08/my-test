import json
import os
from datetime import datetime

import pandas as pd
import pytz

from models import Update_extension_services, db


def add_should_run_column(df):
    brazil_now = get_brazil_datetime()
    df["LAST_RUN"] = pd.to_datetime(df["LAST_RUN"], errors="coerce")
    df = df.dropna(subset=["LAST_RUN"])

    current_time = brazil_now

    time_diff_minutes = (current_time - df["LAST_RUN"]).dt.total_seconds() / 60
    # print(f"time diff in minutes:\n{time_diff_minutes}")

    df["SHOULD_RUN"] = time_diff_minutes > df["RUN_AFTER"]

    df.loc[df["RUN_STATUS"] == 0, "SHOULD_RUN"] = False

    return df


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def verify_current_status():
    update_extension_server_df = model_to_dataframe(Update_extension_services)
    update_extension_server_df = add_should_run_column(update_extension_server_df)
    # print(f"Current df data : \n {update_extension_server_df}")


def get_actions_actual_status():
    verify_current_status()
    update_extension_server_df = model_to_dataframe(Update_extension_services)
    actions_dict = update_extension_server_df.to_dict(orient="records")
    return actions_dict


def get_brazil_datetime():
    """Returns the current datetime in Brazil/Sao_Paulo timezone as a naive datetime."""
    utc_now = datetime.now(pytz.utc)
    brazil_tz = pytz.timezone("America/Sao_Paulo")
    brazil_now = utc_now.astimezone(brazil_tz)
    return brazil_now.replace(tzinfo=None)  # Convert to naive datetime


class UPDATE_EXTENSION_STATUS:
    def __init__(self, ACTION):
        self.ACTION = ACTION

    def get_action_register(self):
        return (
            db.session.query(Update_extension_services)
            .filter_by(ACTION=self.ACTION)
            .first()
        )

    def update_run_status(self, RUN_STATUS):
        # Options for run status  Not Running -  0 , Running - 1 , runned = 2   -1 - Error
        brazil_now = get_brazil_datetime()
        ACTION_REGISTER = self.get_action_register()
        ACTION_REGISTER.RUN_STATUS = RUN_STATUS
        ACTION_REGISTER.LAST_RUN = brazil_now
        ACTION_REGISTER.LAST_UPDATE = brazil_now
        db.session.commit()
        return ACTION_REGISTER

    def update_progress_value(self, RUN_STATUS):
        brazil_now = get_brazil_datetime()
        ACTION_REGISTER = self.get_action_register()
        ACTION_REGISTER.PROGRESS_VALUE = RUN_STATUS
        ACTION_REGISTER.LAST_UPDATE = brazil_now
        db.session.commit()
        return ACTION_REGISTER
