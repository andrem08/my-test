import json
import os
import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd
import pytz

from models import NF_Service, NF_ServiceMetadata, ServiceNFReport, db

# --- UTILITY FUNCTIONS ---


def parse_decimal(value, precision=None) -> Decimal:
    """
    Parses any value into a Decimal, with optional rounding.
    """
    if isinstance(value, Decimal):
        if precision is not None:
            quantizer = Decimal("1e-" + str(precision))
            return value.quantize(quantizer, rounding=ROUND_HALF_UP)
        return value

    if value is None or value == "":
        return Decimal("0.0")

    # Convert numbers to string to handle them uniformly
    if isinstance(value, (int, float)):
        value = str(value)

    cleaned_value = str(value)
    if "," in cleaned_value and "." in cleaned_value:
        cleaned_value = cleaned_value.replace(".", "").replace(",", ".")
    elif "," in cleaned_value:
        cleaned_value = cleaned_value.replace(",", ".")

    try:
        decimal_value = Decimal(cleaned_value)
        if precision is not None:
            quantizer = Decimal("1e-" + str(precision))
            return decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP)
        return decimal_value
    except Exception:
        return Decimal("0.0")


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def get_row_as_dict(df: pd.DataFrame, column: str, value) -> dict:
    row = df.loc[df[column] == value]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def timestamp_to_brazil_time(timestamp) -> str:
    if not timestamp:
        return ""
    try:
        brt_tz = pytz.timezone("America/Sao_Paulo")
        dt_object = datetime.fromtimestamp(int(timestamp), brt_tz)
        return dt_object.strftime("%d/%m/%Y %H:%M:%S")
    except (ValueError, TypeError):
        return ""


def group_elements_by_key(input_array, key):
    grouped_elements = {}
    for element in input_array:
        element_key = element.get(key)
        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []
            grouped_elements[element_key].append(element)
    return list(grouped_elements.values())


# --- DATABASE INTERACTION ---


def create_service_nf_report_item(data):
    # Convert Decimals back to strings for db.Text columns
    for key, value in data.items():
        if isinstance(value, Decimal):
            data[key] = str(value)
    new_register = ServiceNFReport(**data)
    db.session.add(new_register)
    db.session.commit()


def get_element_by_rps(rps):
    return db.session.query(ServiceNFReport).filter_by(RPS=rps).first()


def edit_existing_element(rps, data_dict, keys_to_update):
    existing_element = get_element_by_rps(rps)
    if existing_element is None:
        return None

    for key in keys_to_update:
        if key in data_dict:
            value = data_dict[key]
            # Convert Decimals back to strings
            if isinstance(value, Decimal):
                setattr(existing_element, key, str(value))
            else:
                setattr(existing_element, key, value)

    existing_element.updated_at = datetime.utcnow()
    db.session.commit()
    return existing_element


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        val_db = reg_db.get(key)
        val_api = reg_api.get(key)

        if val_db != val_api:
            print(
                f"(DIVERGENCE) Key: '{key}' -> DB: {val_db} ({type(val_db)}) <-> API: {val_api} ({type(val_api)})",
                flush=True,
            )
            return True
    return False


# --- MAIN CLASS ---


def merge_dataframes_inner(df1, df2, key1, key2):
    try:
        merged_df = pd.merge(df1, df2, left_on=key1, right_on=key2, how="inner")
        print("DataFrames merged successfully.")
        return merged_df
    except KeyError as e:
        print(f"An error occurred during merge: A key column was not found. {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during merge: {e}")
        return None


def save_df_to_csv(dataframe, file_path):
    try:
        # Use the to_csv method to save the DataFrame
        # index=False prevents pandas from writing the DataFrame index as a column
        dataframe.to_csv(file_path, index=False, encoding="utf-8")
        print(f"DataFrame successfully saved to {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def remove_duplicate_keys(dataframe, key_column):
    try:
        # The 'duplicated' method with keep=False marks all occurrences of duplicates as True.
        # We use the ~ (tilde) operator to invert this boolean Series, keeping only unique rows.
        is_duplicate = dataframe.duplicated(subset=[key_column], keep=False)
        df_no_duplicates = dataframe[~is_duplicate]

        print(f"Removed rows with duplicate keys in column '{key_column}'.")
        return df_no_duplicates
    except KeyError:
        print(
            f"An error occurred: Key column '{key_column}' not found in the DataFrame."
        )
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def query_row_as_dict(dataframe, key_column, key_value):

    try:
        # Filter the dataframe to find matching rows
        result_df = dataframe[dataframe[key_column] == key_value]

        # Check if any rows were found
        if not result_df.empty:
            # Get the first matching row and convert it to a dictionary
            row_dict = result_df.iloc[0].to_dict()
            print(f"Found row for key '{key_value}' in column '{key_column}'.")
            return row_dict
        else:
            print(f"No row found for key '{key_value}' in column '{key_column}'.")
            return None
    except KeyError:
        print(
            f"An error occurred: Key column '{key_column}' not found in the DataFrame."
        )
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


class SERVICE_NF_REPORT_MANAGE:
    def __init__(self, data):
        self.api_source = data
        self.all = []
        self.service_nf_df = model_to_dataframe(NF_Service)
        self.service_nf_metadata_df = model_to_dataframe(NF_ServiceMetadata)
        self.service_nf_general_info_df = merge_dataframes_inner(
            self.service_nf_df, self.service_nf_metadata_df, "id_servico", "codigo"
        )
        self.service_nf_general_info_df_cleaned = remove_duplicate_keys(
            self.service_nf_general_info_df, "numeronfs"
        )

    def get_cc_ref(self, rps):
        NF_referenced = query_row_as_dict(
            self.service_nf_general_info_df_cleaned, "numeronfs", rps
        )
        cc_reference = NF_referenced.get("cc_ref", "-1")
        return cc_reference

    def verify_elements(self):
        registers = self.api_source
        for register in registers:
            service_nf_reference = get_row_as_dict(
                self.service_nf_df, "id_pedido", register.get("RPS")
            )

            # Safely get cc_ref and obs_interno_pedido, ensuring they are strings
            cc_ref = "-1"
            obs_interno = "-1"
            if service_nf_reference:
                cc_ref = str(service_nf_reference.get("cc_ref", "-1"))
                obs_interno = str(service_nf_reference.get("obs_interno_pedido", "-1"))
                rps = register.get("RPS")
                if cc_ref == "-1":
                    cc_ref = self.get_cc_ref(rps)

            register_dict = {
                "ID": register.get("ID"),
                "RPS": register.get("RPS"),
                "Nota": register.get("Nota"),
                "Cliente": register.get("Cliente"),
                "CNPJ": register.get("CNPJ"),
                "Endereco": register.get("Endereco"),
                "Numero": register.get("Numero"),
                "Complemento": register.get("Complemento"),
                "Bairro": register.get("Bairro"),
                "Cidade": register.get("Cidade"),
                "Estado": register.get("Estado"),
                "CEP": register.get("CEP"),
                "Email": register.get("Email"),
                "Telefone": register.get("Telefone"),
                "Vendedor": register.get("Vendedor"),
                "ValorServicos": parse_decimal(
                    register.get("ValorServicos"), precision=2
                ),
                "ValorTotal": parse_decimal(register.get("ValorTotal"), precision=2),
                "TotalParcelas": register.get("TotalParcelas"),
                "ValorDeducoes": parse_decimal(
                    register.get("ValorDeducoes"), precision=2
                ),
                "Aliquota": register.get("Aliquota"),
                "ValorISS": parse_decimal(register.get("ValorISS"), precision=2),
                "ISSRetido": register.get("ISSRetido"),
                "ValorCOFINS": parse_decimal(register.get("ValorCOFINS"), precision=2),
                "ValorPIS": parse_decimal(register.get("ValorPIS"), precision=2),
                "ValorCSLL": parse_decimal(register.get("ValorCSLL"), precision=2),
                "ValorIR": parse_decimal(register.get("ValorIR"), precision=2),
                "ValorINSS": parse_decimal(register.get("ValorINSS"), precision=2),
                "ValorTributos": parse_decimal(
                    register.get("ValorTributos"), precision=2
                ),
                "DataPedido": timestamp_to_brazil_time(register.get("DataPedido")),
                "LocalPrestacao": register.get("LocalPrestacao"),
                "Contas": register.get("Contas"),
                "Chave": register.get("Chave"),
                "Protocolo": register.get("Protocolo"),
                "Descricao": register.get("Descricao"),
                "DataEmissao": timestamp_to_brazil_time(register.get("DataEmissao")),
                "Situacao": register.get("Situacao"),
                "DataCad": timestamp_to_brazil_time(register.get("DataCad")),
                "DataMod": timestamp_to_brazil_time(register.get("DataMod")),
                "cc_ref": cc_ref,
                "ObservacoesInternas": obs_interno,
                "source": "api",
            }
            self.all.append(register_dict)

    def verify_elements_bd(self):
        registers_db = ServiceNFReport.query.all()
        for register in registers_db:
            register_dict = {
                c.name: getattr(register, c.name) for c in register.__table__.columns
            }

            # Standardize all numeric and text fields from the database
            for key in [
                "ValorServicos",
                "ValorTotal",
                "ValorDeducoes",
                "ValorISS",
                "ValorCOFINS",
                "ValorPIS",
                "ValorCSLL",
                "ValorIR",
                "ValorINSS",
                "ValorTributos",
            ]:
                register_dict[key] = parse_decimal(register_dict.get(key), precision=2)

            register_dict["cc_ref"] = str(register_dict.get("cc_ref", "-1"))
            register_dict["source"] = "db"
            self.all.append(register_dict)

    def get_updates(self):
        print("Iniciando SERVICE NF REPORT MANAGER")
        self.verify_elements()
        self.verify_elements_bd()

        keys_to_compare = [
            c.name
            for c in ServiceNFReport.__table__.columns
            if c.name not in ["ID", "RPS", "created_at", "updated_at"]
        ]
        grouped_arrays = group_elements_by_key(self.all, "RPS")

        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        print(
                            f"Creating new service report with RPS: {group[0].get('RPS')}"
                        )
                        data_to_create = group[0].copy()
                        data_to_create.pop("source", None)
                        data_to_create["created_at"] = datetime.now()
                        data_to_create["updated_at"] = datetime.now()
                        create_service_nf_report_item(data_to_create)
                    except Exception as e:
                        print(
                            f"An error occurred while creating RPS {group[0].get('RPS')}: {e}"
                        )

            elif len(group) == 2:
                api_reg = group[0] if group[0]["source"] == "api" else group[1]
                db_reg = group[0] if group[0]["source"] == "db" else group[1]

                if are_registers_divergent(db_reg, api_reg, keys_to_compare):
                    try:
                        print(
                            f"Updating existing service report with RPS: {api_reg.get('RPS')}"
                        )
                        edit_existing_element(
                            api_reg.get("RPS"), api_reg, keys_to_compare
                        )
                    except Exception as e:
                        print(
                            f"An error occurred while editing RPS {api_reg.get('RPS')}: {e}"
                        )

        print("Finalizando SERVICE NF REPORT MANAGER")
        return {"message": "Manage service nf report updated"}
