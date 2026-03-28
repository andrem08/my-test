import json
import os
from concurrent.futures import (  # Import for parallelism
    ThreadPoolExecutor,
    as_completed,
)
from datetime import datetime
from decimal import Decimal

import requests
from dotenv import load_dotenv
from tqdm import tqdm

from models import Merch_entry, Product_entry, db
from utils.data_converter import DataConverter


def json_serializer(obj):
    """
    Custom JSON serializer for datetime and Decimal objects.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def are_registers_divergent(reg_api, reg_db, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            print(f"The key {key} are divergent", flush=True)
            print(f"API {reg_api[key]} -  DB {reg_db[key]}", flush=True)
            print(f"API {reg_api}", flush=True)
            print(f"DB {reg_db}", flush=True)
            return True
    return False


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def transform_and_save_dict_array_to_json(data_array, file_path):
    """
    Transforms an array of dictionaries, handling specific date formats,
    and saves the result to a JSON file.

    Args:
        data_array (list of dict): The input array of dictionaries.
        file_path (str): The path to the output JSON file.
    """

    processed_data = []

    def _parse_and_handle_date(date_string):
        """
        Internal helper to parse an ISO 8601 string into a datetime object.
        Handles '0000-00-00 00:00:00' by returning None.
        """
        if not date_string:
            return None
        if date_string == "0000-00-00 00:00:00":
            return None
        try:
            if isinstance(date_string, str):
                return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            return date_string
        except (ValueError, TypeError):
            print(
                f"Warning: Could not parse '{date_string}' as a valid date/time. Setting to None.",
                flush=True,
            )
            return None

    def _verify_numeric_float(number):
        """Internal helper to convert to float, returns None on error."""
        if isinstance(number, (float, int)):
            return float(number)
        try:
            return float(number)
        except (ValueError, TypeError):
            return None

    def _verify_numeric_int(number):
        """Internal helper to convert to int, returns -1 on error or empty/None."""
        if number == "" or number is None:
            return -1
        try:
            return int(number)
        except (ValueError, TypeError):
            return -1

    for original_dict in data_array:
        transformed_dict = {}
        for key, value in original_dict.items():
            if "data_" in key or "created_at" in key or "updated_at" in key:
                transformed_dict[key] = _parse_and_handle_date(value)
            elif (
                "valor_" in key
                or "desconto_" in key
                or "peso_" in key
                or "frete_" in key
            ):
                transformed_dict[key] = _verify_numeric_float(value)
            elif "id_" in key and key not in [
                "id_entrada",
                "id_pedido",
                "id_cliente",
                "id_transportadora",
                "id_centro_custos",
            ]:  # Add more specific ID handling if needed
                transformed_dict[key] = _verify_numeric_int(value)
            else:
                transformed_dict[key] = value
        processed_data.append(transformed_dict)

    with open(file_path, "w") as json_file:
        json.dump(processed_data, json_file, default=json_serializer, indent=4)


class VHSYS_PRODUCT_ENTRY:
    def __init__(self):
        load_dotenv()
        self.url = "https://api.vhsys.com/v2/entradas-mercadoria"
        self.merch_ids = []
        self.new = []
        self.api_elements = []
        self.db_elements = []
        self.all = []
        self.insertion_logs = []
        self.error_logs = []
        self.raw_api = []
        self.ACESS_TOKEN = os.getenv("vhsys_acess_token")
        self.SECRET_ACESS_TOKEN = os.getenv("vhsys_secret_Access_Token")

    def get_merch_ids(self):
        print("Getting merch ids")
        registers_db = Merch_entry.query.all()
        for register in registers_db:
            register_dict = {
                "id_entrada": register.id_entrada,
                "source": "db_merch_table",
            }
            self.merch_ids.append(register_dict)

    def create_element(self, register):
        print(f"Creating register { register } ")
        new_product = Product_entry(
            id_ped_produto=register["id_ped_produto"],
            id_entrada=register["id_entrada"],
            id_produto=register["id_produto"],
            id_almoxarifado=register["id_almoxarifado"],
            id_lote=register["id_lote"],
            desc_produto=register["desc_produto"],
            qtde_produto=register["qtde_produto"],
            unidade_produto=register["unidade_produto"],
            desconto_produto=register["desconto_produto"],
            ipi_produto=register["ipi_produto"],
            icms_produto=register["icms_produto"],
            cfop_produto=register["cfop_produto"],
            ncm_produto=register["ncm_produto"],
            valor_unit_produto=register["valor_unit_produto"],
            valor_total_produto=register["valor_total_produto"],
            peso_produto=register["peso_produto"],
            peso_liq_produto=register["peso_liq_produto"],
            json_localizacoes=register["json_localizacoes"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.session.add(new_product)
        db.session.commit()

    def get_products_list(self):
        registers_db = Product_entry.query.all()

        for register in registers_db:
            register_dict = {
                "id_ped_produto": register.id_ped_produto,
                "id_entrada": register.id_entrada,
                "id_produto": register.id_produto,
                "id_almoxarifado": register.id_almoxarifado,
                "id_lote": register.id_lote,
                "desc_produto": register.desc_produto,
                "qtde_produto": register.qtde_produto,
                "unidade_produto": register.unidade_produto,
                "desconto_produto": register.desconto_produto,
                "ipi_produto": register.ipi_produto,
                "icms_produto": register.icms_produto,
                "cfop_produto": register.cfop_produto,
                "ncm_produto": register.ncm_produto,
                "valor_unit_produto": register.valor_unit_produto,
                "valor_total_produto": register.valor_total_produto,
                "peso_produto": register.peso_produto,
                "peso_liq_produto": register.peso_liq_produto,
                "json_localizacoes": register.json_localizacoes,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def _fetch_merchandise_products(self, entry_id):
        """
        Helper function to fetch products for a single entry_id.
        This will be run in parallel.
        """
        url = f"https://api.vhsys.com/v2/entradas-mercadoria/{entry_id}/produtos"

        headers = {
            "access-token": self.ACESS_TOKEN,
            "secret-access-token": self.SECRET_ACESS_TOKEN,
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return entry_id, response.json()
        except requests.exceptions.HTTPError as http_err:
            print(
                f"HTTP error occurred for entry ID {entry_id}: {http_err}", flush=True
            )

            return entry_id, None
        except requests.exceptions.RequestException as err:
            print(
                f"A network or request error occurred for entry ID {entry_id}: {err}",
                flush=True,
            )
            return entry_id, None
        except Exception as e:
            print(
                f"An unexpected error occurred for entry ID {entry_id} during fetch: {e}",
                flush=True,
            )
            return entry_id, None

    def request_merch_ids_products(self):
        print("Requesting products from API (parallelized)...")

        entry_ids_to_fetch = [
            merch_entry.get("id_entrada")
            for merch_entry in self.merch_ids
            if merch_entry.get("id_entrada")
        ]

        MAX_WORKERS = 10

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_entry_id = {
                executor.submit(self._fetch_merchandise_products, entry_id): entry_id
                for entry_id in entry_ids_to_fetch
            }

            for future in tqdm(
                as_completed(future_to_entry_id),
                total=len(entry_ids_to_fetch),
                desc="Processing Merch Entries",
            ):
                entry_id = future_to_entry_id[future]
                try:
                    fetched_entry_id, product_reg_response = future.result()
                    if product_reg_response and "data" in product_reg_response:
                        products_data = product_reg_response["data"]
                        for product in products_data:
                            self.add_api_product(product)
                    elif product_reg_response is None:
                        print(
                            f"No response received for entry ID: {fetched_entry_id}. Skipping.",
                            flush=True,
                        )
                    else:
                        print("We have a problem here")

                except Exception as e:
                    print(
                        f"An error occurred while retrieving result for entry ID {entry_id}: {e}",
                        flush=True,
                    )
                    self.error_logs.append(
                        f"Error processing result for entry ID {entry_id}: {e}"
                    )

    def add_api_product(self, register):
        product_schema = {
            "id_ped_produto": str,
            "id_entrada": str,
            "id_produto": str,
            "id_almoxarifado": str,
            "id_lote": str,
            "desc_produto": str,
            "qtde_produto": str,
            "unidade_produto": str,
            "desconto_produto": float,
            "ipi_produto": float,
            "icms_produto": float,
            "cfop_produto": str,
            "ncm_produto": float,
            "valor_unit_produto": str,
            "valor_total_produto": str,
            "peso_produto": float,
            "peso_liq_produto": float,
            "json_localizacoes": str,
        }
        product_converter = DataConverter(type_schema=product_schema)
        register_dict = product_converter.convert(register)
        register_dict["source"] = "api"
        self.all.append(register_dict)
        self.api_elements.append(register_dict)
        self.raw_api.append(register)

    def get_updates(self):
        self.get_merch_ids()
        self.request_merch_ids_products()
        self.get_products_list()
        keys_array = []
        grouped_arrays = group_elements_by_key(self.all, "id_ped_produto")

        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        print(f"Elemento {group[0]} sera criado")
                        self.create_element(group[0])

                    except Exception as e:
                        print(f"An error occurred: {e}")
            # if len(group) == 2:
            #    if are_registers_divergent(group[0], group[1], keys_array):
            #        try:
            #            print(f"Elemento { group[0]} sera editado")
            #        except Exception as e:
            #            print(f"An error occurred: {e}")

        # print(f"DB ELEMENTS HERE  {self.db_elements}")

        return {
            "message": "Product updated",
        }
