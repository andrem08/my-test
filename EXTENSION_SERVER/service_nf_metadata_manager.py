import json
import os
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import class_mapper

from models import NF_ServiceMetadata, db


# ✅ Function to create a new service NF metadata record
def create_service_nf_metadata(data):
    if not data.get("codigo"):  # Ensure primary key is present
        print("⚠️ Skipping insert due to missing primary key (codigo):", data)
        return  # Stop execution if codigo is missing

    new_register_data = NF_ServiceMetadata(
        codigo=data.get("codigo"),
        contas=data.get("contas"),
        boletos=data.get("boletos"),
        nota=data.get("nota"),
        cliente=data.get("cliente"),
        status=data.get("status"),
        vendedor=data.get("vendedor"),
        chave=data.get("chave"),
        numeronfs=data.get("numeronfs"),
        notarecibo=data.get("notarecibo"),
        vinculooscomnfs=data.get("vinculooscomnfs"),
        runned=0,
    )

    db.session.add(new_register_data)
    db.session.commit()



def get_register_data_by_id(id):
    return db.session.query(NF_ServiceMetadata).filter_by(codigo=id).first()


def edit_existing_element(id, data_dict, keys_to_update):
    existing_element = get_register_data_by_id(id)

    if existing_element is None:
        return None

    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_element, key, data_dict[key])

    existing_element.updated_at = datetime.utcnow()
    db.session.commit()

    return existing_element


def model_to_dicts(model, columns=None):
    records = model.query.all()
    if columns is None:
        columns = [column.name for column in model.__table__.columns]
    data = [
        {column: getattr(record, column) for column in columns} for record in records
    ]
    return data


# ✅ Convert a model to a Pandas DataFrame
def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def find_missing_rows(large_df: pd.DataFrame, small_df: pd.DataFrame) -> pd.DataFrame:
    # Ensure id_servico is treated as string for proper matching
    large_df["codigo"] = large_df["codigo"].astype(str)
    small_df["codigo"] = small_df["codigo"].astype(str)

    # Filter out rows where id_servico already exists in large_df
    missing_rows = small_df[~small_df["codigo"].isin(large_df["codigo"])]

    return missing_rows


def update_service_nf_metadata_from_diff(diff_row: dict):
    # Get the service ID
    codigo_id = diff_row.get("codigo")
    if not codigo_id:
        print("⚠️ Missing codigo in diff row")
        return

    # Get existing record
    existing = get_register_data_by_id(codigo_id)
    if not existing:
        print(f"⚠️ Record with codigo  {codigo_id} not found")
        return

    # Map of API fields to database fields
    changes = {}
    for key, api_value in diff_row.items():
        if key.endswith("_api"):
            db_field = key[:-4]  # Remove '_api' suffix
            db_value = diff_row.get(f"{db_field}_db")

            # Only update if the value actually changed
            if api_value != db_value:
                # Convert numeric fields from "1,00" format to float
                if any(substr in db_field for substr in ["aliq", "valor"]):
                    try:
                        api_value = float(api_value.replace(",", "."))
                    except (ValueError, AttributeError):
                        pass  # Leave as-is if conversion fails

                changes[db_field] = api_value

    # Apply changes if any
    if changes:
        print(f"🔄 Updating {codigo_id} with changes:", changes)
        try:
            for key, value in changes.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating {codigo_id}: {str(e)}")
    else:
        print(f"✅ No changes needed for {codigo_id}")


def find_differences(
    db_df: pd.DataFrame, api_df: pd.DataFrame, key_columns: list
) -> pd.DataFrame:
    """Compare two DataFrames and find rows with differing values."""
    # Ensure consistent column order and data types
    cols_to_compare = [col for col in db_df.columns if col not in key_columns]

    # Merge with indicator
    merged = api_df.merge(
        db_df, on=key_columns, suffixes=("_api", "_db"), how="outer", indicator=True
    )

    # Find differences using vectorized operations
    diff_mask = pd.Series(False, index=merged.index)

    for col in cols_to_compare:
        api_col = f"{col}_api"
        db_col = f"{col}_db"

        # Handle NaN values properly
        mask = merged[api_col].fillna("@@NaN@@") != merged[db_col].fillna("@@NaN@@")
        diff_mask |= mask

    # Filter rows where any column differs
    result = merged[diff_mask & (merged["_merge"] == "both")]

    # Clean up merge column
    return result.drop(columns=["_merge"])

def save_df_to_csv(dataframe, file_path):
  """
  Saves a pandas DataFrame to a CSV file.

  Args:
    dataframe (pd.DataFrame): The pandas DataFrame to save.
    file_path (str): The path (including filename) where the CSV will be saved.
                     Example: 'output/my_data.csv'
  """
  try:
    # Use the to_csv method to save the DataFrame
    # index=False prevents pandas from writing the DataFrame index as a column
    dataframe.to_csv(file_path, index=False, encoding='utf-8')
    print(f"DataFrame successfully saved to {file_path}")
  except Exception as e:
    print(f"An error occurred: {e}")

# ✅ Service Metadata Manager Class
class SERVICE_NF_METADATA_MANAGER:
    def __init__(self, data):
        print("\n🔍 Initializing SERVICE_NF_METADATA_MANAGER...")

        # 🔹 Convert API data to DataFrame
        self.api_source_df = data
        print(f"DF HERE {self.api_source_df} ")
        # save_df_to_csv(self.api_source_df, "SERVICE_NF_METADATA_MANAGER.csv")
        # 🔹 Load DB records into DataFrame
        self.db_elements_df = model_to_dataframe(NF_ServiceMetadata)

        # 🔹 Drop timestamp columns (optional)
        if (
            "created_at" in self.db_elements_df.columns
            and "updated_at" in self.db_elements_df.columns
        ):
            self.db_elements_df = self.db_elements_df.drop(
                columns=["created_at", "updated_at", "runned"]
            )

    def get_updates(self):
        print("\n🔄 Checking for updates...")

        # 🔹 Find rows in API data that are missing in DB
        missing_rows = find_missing_rows(self.db_elements_df, self.api_source_df)

        print("\n📌 Missing rows to insert:", len(missing_rows))

        for index, row in missing_rows.iterrows():
            creation_data = row.where(
                pd.notna(row), None
            ).to_dict()  # Replace NaN with None
            print("\n📝 Creating record:", creation_data)

            # Ensure "codigo" is present before inserting
            if creation_data.get("codigo") is not None:
                create_service_nf_metadata(creation_data)

        print("\n✅ Finished processing updates!") 

        rows_with_differences = find_differences(
            self.db_elements_df, self.api_source_df, ["codigo"]
        )
        column_db = self.db_elements_df.columns.tolist()
        column_api = self.api_source_df.columns.tolist()
        unique_elements = list(set(column_db) - set(column_api))
        print("\n \n Unique elements here", unique_elements)
        for index, row in rows_with_differences.iterrows():
            reference_data = row.where(
                pd.notna(row), None
            ).to_dict()  # Replace NaN with None
            print("\n📝 Editing record:", reference_data)
            # update_service_nf_metadata_from_diff(reference_data)
