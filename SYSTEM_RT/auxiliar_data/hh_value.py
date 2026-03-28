import json
from datetime import datetime
from decimal import Decimal

import pandas as pd

from log_jobs.log_jobs import LogJobs
from models import EmployersData, Valor_base_by_employer, db


def model_to_dataframe(model):
    records = model.query.all()
    if not records:
        return pd.DataFrame()  # Return empty DataFrame if no records
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column, None) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


class EXTERNAL_DATA_HH_VALUE:
    def __init__(self):
        self.employers_data_df = model_to_dataframe(EmployersData)
        self.valor_base_by_employer_df = model_to_dataframe(Valor_base_by_employer)
        self.key_employers_data = "matricula_funcionario"
        self.key_valor_base_by_employer = "id_matricula"

    def create_valor_base_by_employer_reg(self, name, id_matricula):
        print(f"Creating new register for user {name} \n \n")
        new_valor_base_by_employer = Valor_base_by_employer(
            id_matricula=id_matricula,
            employer=name,
            valor_base=0,
            adm_percent=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.session.add(new_valor_base_by_employer)
        db.session.commit()

        return new_valor_base_by_employer

    def get_updates(self):
        # If there is no employer data, we can't do anything.
        if self.employers_data_df.empty:
            print("No employer data found. Nothing to update.")
            return {"message": "No employer data found. Nothing to update."}

        # --- THIS IS THE FIX ---
        # Check if the valor_base_by_employer_df is empty.
        # If it is, create an empty list for existing_ids.
        # Otherwise (if it's not empty), get the IDs from the DataFrame column.
        if self.valor_base_by_employer_df.empty:
            print("valor_base_by_employer table is empty. All employers will be added.")
            existing_ids = []  # Use an empty list
        else:
            # This code now only runs if the DataFrame is NOT empty, avoiding the KeyError
            existing_ids = self.valor_base_by_employer_df[
                self.key_valor_base_by_employer
            ].astype(str)
        # --- END OF FIX ---

        main_ids = self.employers_data_df[self.key_employers_data].astype(str)
        
        # This logic now works perfectly, whether existing_ids is empty or not.
        # It will compare main_ids against an empty list, finding all employers.
        final_df = self.employers_data_df[~main_ids.isin(existing_ids)].copy()

        print(f"Users that dont appears in VALOR_BASE_BY_EMPLOYER_TABLE{final_df}")
        users_that_dont_exist = final_df.to_dict(orient="records")
        
        for user in users_that_dont_exist:
            self.create_valor_base_by_employer_reg(
                user["nome_funcionario"], user["matricula_funcionario"]
            )

        return {
            "message": f"HH_value_user updated. {len(users_that_dont_exist)} new users added.",
        }