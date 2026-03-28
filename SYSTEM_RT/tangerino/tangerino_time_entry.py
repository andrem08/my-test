import hashlib
import re
from datetime import timedelta

import pandas as pd
from dotenv import load_dotenv

from models import (
    Clock_Time_Entry,
    Clock_User,
    Current_worked_hours,
    EmployersData,
    Tangerino_entries,
    db,
)

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
    return df.to_dict(orient="records")


def iterate_dict_list(dict_list):
    for entry in dict_list:
        for key, value in entry.items():
            print(f"{key}: {value}")
        print("---")


def create_current_worked_hours(data_dict):
    print(f"\n Novo registro a ser criado {data_dict}")
    new_record = Current_worked_hours(
        ID=data_dict.get("ID"),
        description_CLOCK=data_dict.get("description_CLOCK"),
        interval_duration_minutes_CLOCK=data_dict.get(
            "interval_duration_minutes_CLOCK"
        ),
        email_CLOCK=data_dict.get("email_CLOCK"),
        day_reference_CLOCK=data_dict.get("day_reference_CLOCK"),
        EMPLOYER_TANGERINO=data_dict.get("EMPLOYER_TANGERINO"),
        worked_hours_minutes_TANGERINO=data_dict.get("worked_hours_minutes_TANGERINO"),
        work_expect_minutes_TANGERINO=data_dict.get("work_expect_minutes_TANGERINO"),
        DAY_REF_TANGERINO=data_dict.get("DAY_REF_TANGERINO"),
        token=data_dict.get("token"),
        DAY=data_dict.get("DAY"),
        valid_clock=data_dict.get("valid_clock"),
        valid_tangerino=data_dict.get("valid_tangerino"),
        worked_minus_expected_minutes=data_dict.get("worked_minus_expected_minutes"),
        status=data_dict.get("status"),
        worked_hours_hhmm=data_dict.get("worked_hours_hhmm"),
        expected_hours_hhmm=data_dict.get("expected_hours_hhmm"),
    )
    db.session.add(new_record)
    db.session.commit()
    return new_record


class TangerinoTimeEntry:
    def __init__(self):
        print("Updating tangerino time entries")
        self.df_tangerino = model_to_dataframe(Tangerino_entries)
        self.df_employers_data = model_to_dataframe(EmployersData)
        self.df_clock_time_entry = model_to_dataframe(Clock_Time_Entry)
        self.df_clock_user = model_to_dataframe(Clock_User)

    @staticmethod
    def merge_dataframes_clockfy(df_primary, df_secondary):
        return df_primary.merge(
            df_secondary, left_on="user_id", right_on="id", how="left"
        )

    @staticmethod
    def reformat_date(input_date, output_format="%d/%m/%Y"):
        if isinstance(input_date, str):
            input_date = pd.to_datetime(input_date)
        return input_date.strftime(output_format)

    @staticmethod
    def generate_token(email, day):
        return str(day).strip() + str(email).strip().lower()

    @staticmethod
    def generate_hashed_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def minutes_to_hhmm(minutes):
        if pd.isna(minutes):
            return ""
        try:
            return str(timedelta(minutes=int(minutes)))[:-3]
        except:
            return ""

    def update_report(self):
        print("Updating current report")
        df_employers_data = self.df_employers_data[
            ["nome_funcionario", "cpf_funcionario", "email_funcionario"]
        ].copy()
        df_clock_time_entry = self.df_clock_time_entry[
            [
                "description",
                "user_id",
                "interval_start_moment",
                "interval_end_moment",
                "interval_duration",
                "interval_duration_minutes",
            ]
        ]
        df_clock_user = self.df_clock_user[["id", "email", "name", "profile_pic"]]

        df_clock_merged = self.merge_dataframes_clockfy(
            df_clock_time_entry, df_clock_user
        )
        df_clock_merged["day_reference"] = df_clock_merged[
            "interval_start_moment"
        ].apply(self.reformat_date)

        df_clock_grouped = (
            df_clock_merged.groupby(["email", "day_reference"], dropna=False)
            .agg(
                {
                    "description": lambda x: " ; ".join(
                        str(i) for i in x if pd.notna(i)
                    ),
                    "interval_duration_minutes": "sum",
                    "user_id": "first",
                    "id": "first",
                    "name": "first",
                    "profile_pic": "first",
                }
            )
            .reset_index()
        )

        df_clock_grouped = df_clock_grouped.rename(columns=lambda col: f"{col}_CLOCK")
        df_clock_grouped["token_CLOCK"] = df_clock_grouped.apply(
            lambda row: self.generate_token(
                row["email_CLOCK"], row["day_reference_CLOCK"]
            ),
            axis=1,
        )
        df_clock_grouped["merge_id"] = df_clock_grouped["token_CLOCK"].apply(
            self.generate_hashed_token
        )

        df_tangerino_merged = self.df_tangerino.copy()
        df_tangerino_merged["EMPLOYER_CPF_CLEAN"] = df_tangerino_merged[
            "EMPLOYER_CPF"
        ].apply(clean_cpf)
        df_employers_data = df_employers_data.copy()
        df_employers_data["CPF_FUNCIONARIO_CLEAN"] = df_employers_data[
            "cpf_funcionario"
        ].apply(clean_cpf)

        df_tangerino_merged = df_tangerino_merged.merge(
            df_employers_data,
            left_on="EMPLOYER_CPF_CLEAN",
            right_on="CPF_FUNCIONARIO_CLEAN",
            how="left",
        )

        df_tangerino_merged = df_tangerino_merged.rename(
            columns=lambda col: f"{col}_TANGERINO"
        )
        df_tangerino_merged["token_TANGERINO"] = df_tangerino_merged.apply(
            lambda row: self.generate_token(
                row["email_funcionario_TANGERINO"], row["DAY_REF_TANGERINO"]
            ),
            axis=1,
        )
        df_tangerino_merged["merge_id"] = df_tangerino_merged["token_TANGERINO"].apply(
            self.generate_hashed_token
        )

        df_merged_final = pd.merge(
            df_clock_grouped, df_tangerino_merged, on="merge_id", how="outer"
        )
        df_merged_final["token"] = df_merged_final["token_CLOCK"].combine_first(
            df_merged_final["token_TANGERINO"]
        )

        df_summary = df_merged_final[
            [
                "description_CLOCK",
                "interval_duration_minutes_CLOCK",
                "email_CLOCK",
                "day_reference_CLOCK",
                "EMPLOYER_TANGERINO",
                "worked_hours_minutes_TANGERINO",
                "work_expect_minutes_TANGERINO",
                "DAY_REF_TANGERINO",
                "token",
            ]
        ].copy()

        df_summary["DAY"] = pd.to_datetime(
            df_summary["day_reference_CLOCK"].combine_first(
                df_summary["DAY_REF_TANGERINO"]
            ),
            dayfirst=True,
            errors="coerce",
        )

        df_summary["valid_clock"] = df_summary["day_reference_CLOCK"].notna()
        df_summary["valid_tangerino"] = df_summary["DAY_REF_TANGERINO"].notna()

        worked = pd.to_numeric(
            df_summary["interval_duration_minutes_CLOCK"], errors="coerce"
        )
        expected = pd.to_numeric(
            df_summary["work_expect_minutes_TANGERINO"], errors="coerce"
        )
        df_summary["worked_minus_expected_minutes"] = worked - expected

        df_summary["status"] = df_summary.apply(
            lambda row: "Unknown"
            if pd.isna(row["worked_minus_expected_minutes"])
            else (
                "Overworked"
                if row["worked_minus_expected_minutes"] > 0
                else (
                    "Underworked" if row["worked_minus_expected_minutes"] < 0 else "OK"
                )
            ),
            axis=1,
        )

        df_summary["worked_hours_hhmm"] = worked.apply(self.minutes_to_hhmm)
        df_summary["expected_hours_hhmm"] = expected.apply(self.minutes_to_hhmm)

        df_summary["ID"] = df_summary["token"].apply(self.generate_hashed_token)


        for row in dataframe_to_dict_list(df_summary):
            # print(f"\n Row  here {row}")
            if (
                not db.session.query(Current_worked_hours)
                .filter_by(ID=row["ID"])
                .first()
            ):
                create_current_worked_hours(row)

        return df_summary
