import hashlib
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from psycopg2 import errors as pg_errors
from sqlalchemy.exc import SQLAlchemyError

from models import EmployersData, db


def get_register_data_by_id(id):
    return (
        db.session.query(EmployersData).filter_by(matricula_funcionario=str(id)).first()
    )


def delete_cc_employer_reg_by_id(id):
    print(f" \n \n Delete by element id {id}")
    element_to_delete = db.session.query(EmployersData).filter_by(matricula_funcionario=id).first()

    if element_to_delete:
        db.session.delete(element_to_delete)
        db.session.commit()
        return True
    else:
        return False



def edit_employer_position(id, position_name):
    if pd.isna(id) or id is None or str(id).strip() == "":
        print(f"Skipping update: Invalid or missing 'matricula_funcionario' ID: {id}")
        return None

    matricula = str(id)

    try:
        existing_element = get_register_data_by_id(matricula)

        if existing_element is None:
            print(f"Update failed: No existing element found with ID: {matricula}")
            return None

        existing_element.nome_cargo_funcionario = position_name
        existing_element.updated_at = datetime.utcnow()
        db.session.commit()
        print(f"Record updated successfully for matricula: {matricula}")
        return existing_element

    except Exception as e:
        print(f"An unexpected error occurred while updating {matricula}: {e}")
        db.session.rollback()
        return None



def edit_existing_element(id, status_funcionario):
    if pd.isna(id) or id is None or str(id).strip() == "":
        print(f"Skipping update: Invalid or missing 'matricula_funcionario' ID: {id}")
        return None

    matricula = str(id)

    try:
        existing_element = get_register_data_by_id(matricula)

        if existing_element is None:
            print(f"Update failed: No existing element found with ID: {matricula}")
            return None

        existing_element.status_funcionario = status_funcionario
        existing_element.updated_at = datetime.utcnow()
        db.session.commit()
        print(f"Record updated successfully for matricula: {matricula}")
        return existing_element

    except pg_errors.UndefinedFunction as e:
        print(f"DATABASE ERROR (Type Mismatch) while updating {matricula}: {e}")
        db.session.rollback()
        return None
    except SQLAlchemyError as e:
        print(f"SQLAlchemy Error (General DB Issue) while updating {matricula}: {e}")
        db.session.rollback()
        return None
    except Exception as e:
        print(f"An unexpected error occurred while updating {matricula}: {e}")
        db.session.rollback()
        return None


def apply_suffixes_to_dataframe(
    df: pd.DataFrame, suffix: str, key_column: str
) -> pd.DataFrame:

    rename_map = {}

    for col in df.columns:
        rename_map[col] = f"{col}{suffix}"

    return df.rename(columns=rename_map, inplace=False)


def merge_and_compare_dataframes_dual_key(
    df_old: pd.DataFrame,
    df_new: pd.DataFrame,
    left_key_column: str,
    right_key_column: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    left_key_suffixed = f"{left_key_column}_db"
    right_key_suffixed = f"{right_key_column}_api"

    df_old_suffixed = apply_suffixes_to_dataframe(df_old, "_db", left_key_column)
    df_new_suffixed = apply_suffixes_to_dataframe(df_new, "_api", right_key_column)

    merged_df = pd.merge(
        df_old_suffixed,
        df_new_suffixed,
        left_on=left_key_suffixed,
        right_on=right_key_suffixed,
        how="outer",
        indicator="_merge",
    )

    only_in_old_df = merged_df[merged_df["_merge"] == "left_only"]
    only_in_new_df = merged_df[merged_df["_merge"] == "right_only"]

    return merged_df, only_in_old_df, only_in_new_df


def generate_hash(input_string):
    hash_object = hashlib.sha256()
    hash_object.update(str(input_string).encode())
    return hash_object.hexdigest()


def model_to_dataframe(model):
    records = model.query.all()
    if not records:
        return pd.DataFrame()

    columns = [c.key for c in model.__mapper__.columns]
    data = [{col: getattr(rec, col) for col in columns} for rec in records]

    return pd.DataFrame(data)


def array_of_dicts_to_dataframe(data_array: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(data_array)

    if "matricula_funcionario" in df.columns:
        df["matricula_funcionario"] = df["matricula_funcionario"].astype(str)

    if "Matricula" in df.columns:
        df["Matricula"] = df["Matricula"].astype(str)

    return df

def filter_dict_array(data_array, key, value):

  return [d for d in data_array if d.get(key) == value]
class EMPLOYERS_MANAGE_CURRENT_STATUS:

    API_KEY_COLUMN = "Matricula"
    DB_KEY_COLUMN = "matricula_funcionario"

    def __init__(self, data):
        self.api_source = data
        self.previous_employers_data = model_to_dataframe(EmployersData)
        if self.DB_KEY_COLUMN in self.previous_employers_data.columns:
            self.previous_employers_data[self.DB_KEY_COLUMN] = (
                self.previous_employers_data[self.DB_KEY_COLUMN].astype(str)
            )
        print(f"\n \n \n Or api element data {data}")
        


    def add_current_employers_position(self): 
        
        print(f"Adding current employers position {self.api_source}")  
        db_employers = self.previous_employers_data.to_dict(orient='records')  
        for emp in db_employers: 
            # print(f"\n Employer here {emp}")
            reg_number_employer_db = emp.get("matricula_funcionario")
            position_employer_db = emp.get("nome_cargo_funcionario") 
            # print(f"\n \n Employer MATRICULA {reg_number_employer_db} CARGO {position_employer_db}")
            api_reg = filter_dict_array(self.api_source,"Matricula", reg_number_employer_db)
            # print(f" \n \n API REG {api_reg}")
            employer_name = emp.get("nome_funcionario")
            if(api_reg[0].get("Cargo")):
                api_cargo = api_reg[0].get("Cargo")
                print(f"\n EMPLOYER {employer_name}  Cargo {api_cargo} (API) - {position_employer_db} (DB)",flush=True)
                if(api_cargo != position_employer_db):
                    print("Precisamos editar o nosso banco de dados")
                    edit_employer_position(reg_number_employer_db,api_cargo)
                    print(" \n \n Cargo editado")
            else:
                print("Não temos este registro")

    def get_updates(self):
        print("Starting data reconciliation...")
        self.add_current_employers_position()
        api_df = array_of_dicts_to_dataframe(self.api_source)

        merged_all, only_in_db, only_in_api = merge_and_compare_dataframes_dual_key(
            df_old=self.previous_employers_data,
            df_new=api_df,
            left_key_column=self.DB_KEY_COLUMN,
            right_key_column=self.API_KEY_COLUMN,
        )

        effective_key = f"{self.DB_KEY_COLUMN}_db"
        # print(f" \n \n \n Only in api elements {only_in_api}")

        print(f"\nReconciliation complete. Effective merge key: '{effective_key}'.")
        print(f"Records only in DB (Potential Deletions): {len(only_in_db)}")
        print(f"Records only in API (Potential Additions): {len(only_in_api)}")

        updates_count = 0
        for index, row in merged_all.iterrows():

            status_api = row.get("Status_api")
            status_db = row.get("status_funcionario_db")
            matricula = row.get(effective_key)

            if pd.isna(matricula):
                continue

            if status_api != status_db:

                updated_element = edit_existing_element(matricula, status_api)
                if updated_element:
                    updates_count += 1

        print(f"\nCompleted status updates. Total records updated: {updates_count}")

        for index, row in only_in_db.iterrows():
            row_dict = row.to_dict()
            matricula = row_dict.get("matricula_funcionario_db")
            print(f"Row that should be deleted {index} as Dictionary: {row_dict}")
            print(f"Matricula  {matricula}")
            delete_cc_employer_reg_by_id(matricula)
        return merged_all, only_in_db, only_in_api
