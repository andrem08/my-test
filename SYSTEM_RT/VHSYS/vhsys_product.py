import logging
import os
from datetime import datetime
from decimal import Decimal

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy.exc import DataError, IntegrityError, OperationalError
from tqdm import tqdm

from models import Product, db
from utils.data_converter import DataConverter
from VHSYS.api import api_results, api_results_by_page_limit, api_results_parallel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def model_to_dataframe(model):
    records = model.query.all()
    if not records:
        return pd.DataFrame()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column, None) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def group_elements_by_key(input_array, key):
    grouped_elements = {}
    for element in input_array:
        element_key = element.get(key)
        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []
            grouped_elements[element_key].append(element)
    return list(grouped_elements.values())


def compare_values(value1, value2):
    try:
        return Decimal(str(value1)) == Decimal(str(value2))
    except (ValueError, TypeError):
        try:
            date_format = "%Y-%m-%d"
            date_value1 = datetime.strptime(str(value1).split(" ")[0], date_format)
            date_value2 = datetime.strptime(str(value2).split(" ")[0], date_format)
            return date_value1 == date_value2
        except (ValueError, TypeError):
            return str(value1) == str(value2)


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        if not compare_values(reg_db.get(key), reg_api.get(key)):
            return True
    return False


class VHSYS_PRODUCT:
    def __init__(self):
        load_dotenv()
        self.url = "https://api.vhsys.com/v2/produtos"
        self.api_elements = []
        self.db_elements = []
        self.all = []
        self.insertion_logs = []
        self.error_logs = []
        self.ACESS_TOKEN = os.getenv("vhsys_acess_token")
        self.SECRET_ACESS_TOKEN = os.getenv("vhsys_secret_Access_Token")

    def create_register(self, data: dict):
        try:
            logger.info(
                f"Attempting to create a product record with data for id_produto: {data.get('id_produto')}"
            )

            new_product = Product(
                id_produto=data["id_produto"],
                id_registro=data["id_registro"],
                id_empresa=data["id_empresa"],
                id_categoria=data["id_categoria"],
                cod_produto=data["cod_produto"],
                marca_produto=data["marca_produto"],
                desc_produto=data["desc_produto"],
                atalho_produto=data["atalho_produto"],
                fornecedor_produto=data["fornecedor_produto"],
                fornecedor_produto_id=data["fornecedor_produto_id"],
                produto_variado=data["produto_variado"],
                id_produto_parent=data["id_produto_parent"],
                minimo_produto=data["minimo_produto"],
                maximo_produto=data["maximo_produto"],
                estoque_produto=data["estoque_produto"],
                unidade_produto=data["unidade_produto"],
                valor_produto=data["valor_produto"],
                valor_custo_produto=data["valor_custo_produto"],
                peso_produto=data["peso_produto"],
                peso_liq_produto=data["peso_liq_produto"],
                icms_produto=data["icms_produto"],
                ipi_produto=data["ipi_produto"],
                pis_produto=data["pis_produto"],
                cofins_produto=data["cofins_produto"],
                unidade_tributavel=data["unidade_tributavel"],
                cest_produto=data["cest_produto"],
                beneficio_fiscal=data["beneficio_fiscal"],
                ncm_produto=data["ncm_produto"],
                origem_produto=data["origem_produto"],
                codigo_barra_produto=data["codigo_barra_produto"],
                codigo_barras_internos=data["codigo_barras_internos"],
                obs_produto=data["obs_produto"],
                tipo_produto=data["tipo_produto"],
                tamanho_produto=data["tamanho_produto"],
                localizacao_produto=data["localizacao_produto"],
                kit_produto=data["kit_produto"],
                baixar_kit=data["baixar_kit"],
                desmembrar_kit=data["desmembrar_kit"],
                loja_visivel=data["loja_visivel"],
                loja_video_url=data["loja_video_url"],
                valor_tributos=data["valor_tributos"],
                valor_tributosEst=data["valor_tributosEst"],
                status_produto=data["status_produto"],
                id_comissionamento=data["id_comissionamento"],
                id_regra_comissionamento_servico=data[
                    "id_regra_comissionamento_servico"
                ],
                data_cad_produto=data["data_cad_produto"],
                data_mod_produto=data["data_mod_produto"],
                data_mod_estoque=data["data_mod_estoque"],
                lixeira=data["lixeira"],
                endereco_fixo=data["endereco_fixo"],
                controla_lote=data["controla_lote"],
                controla_validade=data["controla_validade"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # --- 2. Database Transaction ---
            db.session.add(new_product)
            db.session.commit()

            logger.info(
                f"Successfully created product with id_produto: {new_product.id_produto}"
            )
            return new_product, None  # Success

        except KeyError as e:
            # Catches errors if a key is missing from the 'data' dictionary
            error_msg = f"Missing data in request: required key '{e}' is missing."
            logger.error(error_msg)
            # No need to rollback here as the transaction hasn't started
            return None, error_msg

        except (IntegrityError, DataError) as e:
            # Catches database constraint violations (e.g., unique key) or data type issues
            db.session.rollback()  # CRITICAL: Roll back the failed transaction
            error_msg = f"Database error: A product with this ID or unique constraint may already exist, or data is invalid. Details: {e.orig}"
            logger.error(error_msg)
            return None, error_msg

        except OperationalError as e:
            # Catches database connection issues
            db.session.rollback()
            error_msg = f"Database connection error: Could not connect to the database. Details: {e.orig}"
            logger.error(error_msg)
            return None, error_msg

        except Exception as e:
            # A general catch-all for any other unexpected errors
            db.session.rollback()
            error_msg = f"An unexpected error occurred: {e}"
            logger.error(error_msg)
            return None, error_msg

    def verify_elements(self):
        registers = api_results(self.url)
        for register in registers:
            print(f"\nProcessing API register: {register.get('id_produto')}")
            register_ref = {
                "id_produto": register.get("id_produto"),
                "id_registro": register.get("id_registro"),
                "id_empresa": register.get("id_empresa"),
                "id_categoria": register.get("id_categoria"),
                "cod_produto": register.get("cod_produto"),
                "marca_produto": register.get("marca_produto"),
                "desc_produto": register.get("desc_produto"),
                "atalho_produto": register.get("atalho_produto"),
                "fornecedor_produto": register.get("fornecedor_produto"),
                "fornecedor_produto_id": register.get("fornecedor_produto_id"),
                "produto_variado": register.get("produto_variado"),
                "id_produto_parent": register.get("id_produto_parent"),
                "minimo_produto": register.get("minimo_produto"),
                "maximo_produto": register.get("maximo_produto"),
                "estoque_produto": register.get("estoque_produto"),
                "unidade_produto": register.get("unidade_produto"),
                "valor_produto": register.get("valor_produto"),
                "valor_custo_produto": register.get("valor_custo_produto"),
                "peso_produto": register.get("peso_produto"),
                "peso_liq_produto": register.get("peso_liq_produto"),
                "icms_produto": register.get("icms_produto"),
                "ipi_produto": register.get("ipi_produto"),
                "pis_produto": register.get("pis_produto"),
                "cofins_produto": register.get("cofins_produto"),
                "unidade_tributavel": register.get("unidade_tributavel"),
                "cest_produto": register.get("cest_produto"),
                "beneficio_fiscal": register.get("beneficio_fiscal"),
                "ncm_produto": register.get("ncm_produto"),
                "origem_produto": register.get("origem_produto"),
                "codigo_barra_produto": register.get("codigo_barra_produto"),
                "codigo_barras_internos": register.get("codigo_barras_internos"),
                "obs_produto": register.get("obs_produto"),
                "tipo_produto": register.get("tipo_produto"),
                "tamanho_produto": register.get("tamanho_produto"),
                "localizacao_produto": register.get("localizacao_produto"),
                "kit_produto": register.get("kit_produto"),
                "baixar_kit": register.get("baixar_kit"),
                "desmembrar_kit": register.get("desmembrar_kit"),
                "loja_visivel": register.get("loja_visivel"),
                "loja_video_url": register.get("loja_video_url"),
                "valor_tributos": register.get("valor_tributos"),
                "valor_tributosEst": register.get("valor_tributosEst"),
                "status_produto": register.get("status_produto"),
                "id_comissionamento": register.get("id_comissionamento"),
                "id_regra_comissionamento_servico": register.get(
                    "id_regra_comissionamento_servico"
                ),
                "data_cad_produto": register.get("data_cad_produto"),
                "data_mod_produto": register.get("data_mod_produto"),
                "data_mod_estoque": register.get("data_mod_estoque"),
                "lixeira": register.get("lixeira"),
                "endereco_fixo": register.get("endereco_fixo"),
                "controla_lote": register.get("controla_lote"),
                "controla_validade": register.get("controla_validade"),
                "source": "api",
            }
            self.api_elements.append(register_ref)
            self.all.append(register_ref)

    def verify_elements_bd(self):
        registers_db = Product.query.all()
        columns = [column.name for column in Product.__table__.columns]
        for register in registers_db:
            # Convert the SQLAlchemy object to a dictionary
            register_dict = {col: getattr(register, col, None) for col in columns}
            register_dict["source"] = "db"
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        print("Fetching elements from API...")
        self.verify_elements()
        print("Fetching elements from Database...")
        self.verify_elements_bd()

        elements = group_elements_by_key(self.all, "id_produto")

        divergent_elements = []

        for group in elements:
            db_reg = next((item for item in group if item.get("source") == "db"), None)
            api_reg = next(
                (item for item in group if item.get("source") == "api"), None
            )

            if len(group) == 1:
                if db_reg:
                    print("\n Only in db")
                if api_reg:
                    print(f"\n Only in api {api_reg}")
                    # Criaremos este elemento
                    self.create_register(api_reg)

            if len(group) > 1:
                if db_reg and api_reg:
                    keys_to_compare = db_reg.keys()
                    if are_registers_divergent(db_reg, api_reg, keys_to_compare):
                        print(
                            f"Divergence found for product ID: {db_reg['id_produto']}"
                        )
                        divergent_elements.append(group)
        print(f"Found {len(divergent_elements)} divergent product groups.")

        return {"message": "Product update check complete."}
