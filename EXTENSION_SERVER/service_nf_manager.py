from datetime import datetime
import pandas as pd

# This line should be active in your project to import your real database model and session.
from models import NF_Service, db

# --- Database Interaction Functions ---

def create_service_nf(data):
    """Creates a new NF_Service record in the database."""
    if not data.get("id_servico"):
        print(f"⚠️ Skipping insert due to missing primary key (id_servico): {data}")
        return

    # Filter the incoming data to only include keys that are valid columns in the NF_Service model.
    valid_columns = [c.key for c in NF_Service.__mapper__.columns]
    
    # Create a new dictionary containing only the data for valid columns.
    filtered_data = {key: data[key] for key in data if key in valid_columns}

    # Use the filtered data to create the new record.
    new_register_data = NF_Service(**filtered_data)
    
    now = datetime.now()
    if 'created_at' in valid_columns:
        new_register_data.created_at = now
    if 'updated_at' in valid_columns:
        new_register_data.updated_at = now

    db.session.add(new_register_data)
    db.session.commit()
    print(f"✅ Created record for id_servico: {filtered_data.get('id_servico')}")


def get_register_data_by_id(service_id):
    """Fetches a single NF_Service record by its primary key."""
    return db.session.query(NF_Service).filter_by(id_servico=service_id).first()


def model_to_dataframe(model):
    """Converts all records from a model to a pandas DataFrame."""
    records = model.query.all()
    if not records:
        return pd.DataFrame()
    
    columns = [c.key for c in model.__mapper__.columns]
    data = [{col: getattr(rec, col) for col in columns} for rec in records]
    
    return pd.DataFrame(data)

# --- Data Comparison and Update Functions ---

def find_missing_rows(db_df: pd.DataFrame, api_df: pd.DataFrame) -> pd.DataFrame:
    """Finds rows in api_df that are not in db_df based on 'id_servico'."""
    if db_df.empty:
        return api_df
    
    db_ids = db_df["id_servico"].astype(str).unique()
    api_ids = api_df["id_servico"].astype(str)
    missing_mask = ~api_ids.isin(db_ids)
    return api_df[missing_mask]


def find_differences(db_df: pd.DataFrame, api_df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    """
    Compares two DataFrames and returns a merged DataFrame with rows
    that have differing values.
    """
    if db_df.empty or api_df.empty:
        return pd.DataFrame()

    db_comp = db_df.copy()
    api_comp = api_df.copy()

    common_cols = list(set(db_comp.columns) & set(api_comp.columns))
    
    for col in common_cols:
        db_comp[col] = db_comp[col].astype(str)
        api_comp[col] = api_comp[col].astype(str)
    
    merged = pd.merge(api_comp[common_cols], db_comp[common_cols], on=key_column, suffixes=("_api", "_db"), how="inner")
    original_merged = pd.merge(api_df, db_df, on=key_column, suffixes=("_api", "_db"), how="inner")

    cols_to_compare = [col for col in common_cols if col != key_column]
    diff_mask = pd.Series(False, index=merged.index)

    for col in cols_to_compare:
        mask = merged[f"{col}_api"].fillna('__nan__') != merged[f"{col}_db"].fillna('__nan__')
        diff_mask |= mask
        
    return original_merged[diff_mask]


def update_service_nf_from_diff(diff_row: dict):
    """
    Updates an existing record and prints a detailed log of what changed.
    """
    service_id = diff_row.get("id_servico")
    if not service_id:
        print("⚠️ Cannot update row due to missing 'id_servico'")
        return

    existing = get_register_data_by_id(service_id)
    if not existing:
        print(f"⚠️ Record with id_servico {service_id} not found in DB for update.")
        return

    detailed_changes = {}
    fields = [key.replace('_api', '') for key in diff_row.keys() if key.endswith('_api')]

    for field in fields:
        api_val = diff_row.get(f"{field}_api")
        db_val = diff_row.get(f"{field}_db")
        
        api_val_comp = str(pd.Series([api_val]).fillna('__nan__').iloc[0])
        db_val_comp = str(pd.Series([db_val]).fillna('__nan__').iloc[0])

        if api_val_comp != db_val_comp:
            detailed_changes[field] = {"old": db_val, "new": api_val}

    if detailed_changes:
        print(f"\n🔄 Updating record '{service_id}':")
        for field, values in detailed_changes.items():
            print(f"  - Field '{field}':")
            print(f"    - Old DB Value:  {values['old']}")
            print(f"    - New API Value: {values['new']}")
        try:
            for field, values in detailed_changes.items():
                setattr(existing, field, values["new"])
            existing.updated_at = datetime.now()
            db.session.commit()
            print(f"✅ Successfully updated '{service_id}' in the database.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating '{service_id}': {str(e)}")

# --- Main Orchestrator Class ---

class SERVICE_NF_MANAGER:
    """Orchestrates the synchronization of NF_Service data."""

    def __init__(self, api_dataframe: pd.DataFrame):
        print("\n🔍 Initializing SERVICE_NF_MANAGER...")
        if not isinstance(api_dataframe, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")
        
        def unbox_tuple(x):
            if isinstance(x, tuple) and len(x) == 1:
                return x[0]
            return x
        
        # ✨ UPDATED: Replaced deprecated 'applymap' with the recommended 'map'. ✨
        self.api_source_df = api_dataframe.map(unbox_tuple)
        
        self.db_elements_df = model_to_dataframe(NF_Service)

    def get_updates(self):
        print("\n🔄 Starting data synchronization process...")

        missing_rows = find_missing_rows(self.db_elements_df, self.api_source_df)
        print(f"\n📌 Found {len(missing_rows)} new records to insert.")
        for index, row in missing_rows.iterrows():
            creation_data = row.to_dict()
            create_service_nf(creation_data)

        rows_with_differences = find_differences(
            self.db_elements_df, self.api_source_df, "id_servico"
        )
        print(f"\n📊 Found {len(rows_with_differences)} records with different data to update.")
        if not rows_with_differences.empty:
            for index, row in rows_with_differences.iterrows():
                update_service_nf_from_diff(row.to_dict())
        
        print("\n✅ Synchronization process finished!")