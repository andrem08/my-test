import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

from cost_center_manager import COST_CENTER_MANAGER
from models import Relatorio_CC, Update_cc_report_status, db

load_dotenv()


def generate_id_token(seed):
    import hashlib

    return hashlib.sha256(seed.encode()).hexdigest()


def are_equal_dicts(dict1, dict2):
    return dict1 == dict2


def df_query_by_params(id_cc, type):
    results = db.session.query(Relatorio_CC).filter_by(ID_CC=id_cc, TYPE=type).all()

    if not results:
        columns = [c.name for c in Relatorio_CC.__table__.columns]
        return pd.DataFrame([], columns=columns)

    data = [row.__dict__ for row in results]

    for item in data:
        item.pop("_sa_instance_state", None)

    df = pd.DataFrame(data)

    return df


def group_equal_dicts(arr):
    grouped_dicts = []
    index = 0
    while arr:
        current_dict = arr.pop(0)
        group = [{"index": index, **current_dict}]
        for other_dict in arr[:]:
            if are_equal_dicts(current_dict, other_dict):
                group.append({"index": index, **other_dict})
                arr.remove(other_dict)
        grouped_dicts.append(group)
        index += 1
    return grouped_dicts


def add_index_to_dicts(data):
    transformed_data = []
    for inner_list in data:
        transformed_inner_list = []
        for index, item in enumerate(inner_list):
            item["index"] = index
            transformed_inner_list.append(item)
        transformed_data.append(transformed_inner_list)
    return transformed_data


def flatten_grouped_dicts_with_index(grouped_dicts):
    flattened = []
    for group in grouped_dicts:
        for item in group:
            flattened.append(item)
    return flattened


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def column_to_array(df, column_name):
    column_values = df[column_name].values
    return column_values


def model_to_dataframe_filtered(model, filter_column, filter_value):
    # Applying filter to the query
    records = model.query.filter_by(**{filter_column: filter_value}).all()
    # Extracting columns
    columns = [column.name for column in model.__table__.columns]
    # Extracting data
    data = [[getattr(record, column) for column in columns] for record in records]
    # Creating DataFrame
    df = pd.DataFrame(data, columns=columns)
    return df


def get_db_registers_by_cc_id_df(id):
    model = model_to_dataframe_filtered(Relatorio_CC, "ID_CC", id)
    # print(f"Model here : {model}", flush=True)
    return model


def extract_date_from_string(string):
    string = string.replace("Pago", "").strip()
    string = string.replace("(", "").strip()
    string = string.replace(")", "").strip()
    date = string.split()[0]
    date_obj = datetime.strptime(date, "%d/%m/%Y")
    date_str = date_obj.isoformat()
    return date_str


def create_relatorio_cc(data):
    print(f" \n \n  Inserindo o registro {data}", flush=True)
    CC_LABEL = data["CC_LABEL"]
    ID_CC = data["CC_ID"]
    CC_MANAGER = COST_CENTER_MANAGER()
    CC = CC_MANAGER.get_cc_label(CC_LABEL)
    NOME_DESPESA = data["NOME_DESPESA"]
    VENCIMENTO = data["VENCIMENTO"]
    SITUACAO = data["SITUACAO"]
    VALOR = data["VALOR"]
    TYPE = data["TYPE"]
    CATEGORIA = data["CATEGORIA"]
    FORNECEDOR = data["FORNECEDOR"]
    VENCIMENTO_DATE = datetime.utcfromtimestamp(int(VENCIMENTO))
    ID = data["ID"]
    ID_SEED = data["ID_SEED"]

    # If the ID doesn't exist, proceed with inserting the new record
    new_relatorio = Relatorio_CC(
        ID=ID,
        ID_SEED=ID_SEED,
        CC=CC,
        ID_CC=ID_CC,
        CC_LABEL=CC_LABEL,
        VENCIMENTO=VENCIMENTO_DATE.isoformat(),
        FORNECEDOR=FORNECEDOR,
        NOME_DESPESA=NOME_DESPESA,
        SITUACAO=SITUACAO,
        DATA_PAGAMENTO=extract_date_from_string(SITUACAO),
        CATEGORIA=CATEGORIA,
        VALOR=VALOR,
        TYPE=TYPE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_relatorio)
    db.session.commit()


def compare_arrays(arr1, arr2):
    set1 = set(arr1)
    set2 = set(arr2)
    only_in_arr1 = set1 - set2
    only_in_arr2 = set2 - set1
    return list(only_in_arr1), list(only_in_arr2)


def get_element_by_key(arr, key, value):
    for item in arr:
        if key in item and item[key] == value:
            return item
    return None


def Update_running_status(cc_id, type_ref):
    # Get the existing ClockUser instance from the database
    update_elem = (
        db.session.query(Update_cc_report_status).filter_by(cc_id=cc_id).first()
    )
    # If the user doesn't exist, you might want to handle that case accordingly
    if update_elem is None:
        # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
        return None
    if type_ref == "entrada":
        update_elem.entries_runned = 1
    if type_ref == "saida":
        update_elem.outputs_runned = 1
    update_elem.updated_at = datetime.utcnow()
    # Commit the changes to the database
    db.session.commit()

    return update_elem


def update_all_cc_status_to_zero():
    # Get all the existing Update_route_status instances from the database
    cc_refs = db.session.query(Update_cc_report_status).all()

    # Loop through each route instance and update its runned field to 0
    for cc_ref in cc_refs:
        cc_ref.entries_runned = 0
        cc_ref.outputs_runned = 0
        cc_ref.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.session.commit()

    return cc_refs


def save_array_to_file(array, folder, filename):
    # Create the folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
    # Construct the full path to the file
    filepath = os.path.join(folder, filename)
    # Write the array elements to the file
    with open(filepath, "w") as f:
        for element in array:
            f.write(str(element) + "\n")


class COST_REPORT_MANAGER:
    # Classe que vai ser ultilizada junto com a nossa extensão para google chrome
    def __init__(self, cc_page_registers):
        self.CC_PAGE = cc_page_registers.get("data")
        self.type = cc_page_registers.get("type")
        self.cc_id_reference = cc_page_registers.get("cc_id")
        self.db_registers_by_cc_id_df = get_db_registers_by_cc_id_df(
            self.cc_id_reference
        )
        self.db_ids_here = column_to_array(self.db_registers_by_cc_id_df, "ID")
        self.extension_ids = []

    def verify_page_is_valid(self):
        data = self.CC_PAGE["source"]
        source = data["subItens"]
        if source:
            return True
        else:
            return False

    @staticmethod
    def delete_cc_report_reg_by_id(id):
        # print(f"Delent element with id {id}", flush=True)
        element_to_delete = db.session.query(Relatorio_CC).filter_by(ID=id).first()

        if element_to_delete:
            db.session.delete(element_to_delete)
            db.session.commit()
            return True
        else:
            return False

    def format_page(self):
        data = self.CC_PAGE
        # print("\n \n  Or data here", data)
        source = data.get("source")
        # cc_id = data.get("cc_id")
        source_itens = source["itens"][0]
        # print(f"\n  Source item {source_itens }")
        CC_LABEL = source.get("itens")[0]["CentroCustos"]
        sub_itens = source["subItens"]["ID1"]
        type_ref = data.get("type")

        CC_ID = self.cc_id_reference
        grouped_regs = group_equal_dicts(sub_itens)
        grouped_regs_data = add_index_to_dicts(grouped_regs)
        flatten_regs_data = flatten_grouped_dicts_with_index(grouped_regs_data)
        # print("Sub itens", flatten_regs_data)

        formated_pages = []

        for sub_item in flatten_regs_data:
            # print(f"\n \n SubItem: {sub_item} \n \n", flush= True)
            index = sub_item.get("index")
            INDEX = index
            VENCIMENTO = sub_item.get("Vencimento")
            FORNECEDOR = sub_item.get("Fornecedor")
            NOME_DESPESA = sub_item.get("NomeDespesa")
            SITUACAO = sub_item.get("Situacao")
            VALOR = sub_item.get("Valor")
            CATEGORIA = sub_item.get("Categoria")
            TYPE = type_ref
            SEED = f"{INDEX}-{CC_ID}-{NOME_DESPESA}-{VENCIMENTO}-{FORNECEDOR}-{VALOR}-{SITUACAO}-{TYPE}-{CATEGORIA}"
            TOKEN = generate_id_token(SEED)

            self.extension_ids.append(TOKEN)

            ref = {
                "INDEX": INDEX,
                "CC_LABEL": CC_LABEL,
                "CC_ID": self.cc_id_reference,
                "VENCIMENTO": VENCIMENTO,
                "FORNECEDOR": FORNECEDOR,
                "NOME_DESPESA": NOME_DESPESA,
                "SITUACAO": SITUACAO,
                "CATEGORIA": CATEGORIA,
                "VALOR": VALOR,
                "ID_SEED": SEED,
                "ID": TOKEN,
                "TYPE": self.type,
            }
            # print("Ref", ref, flush=True)
            # print(f"REF her {ref}")
            formated_pages.append(ref)
        return formated_pages

    @staticmethod
    def compare_dfs_to_dict(
        df1: pd.DataFrame, df2: pd.DataFrame, id_column: str
    ) -> dict:
        # Convert ID columns to sets for fast comparison
        ids_df1 = set(df1[id_column].unique())
        ids_df2 = set(df2[id_column].unique())

        # Find rows only in each DataFrame
        only_in_first = df1[~df1[id_column].isin(ids_df2)]
        only_in_second = df2[~df2[id_column].isin(ids_df1)]

        # Find common IDs
        common_ids = list(ids_df1.intersection(ids_df2))

        # Convert DataFrames to list of dictionaries, ensuring empty list if DataFrame is empty
        only_in_first_list = (
            only_in_first.to_dict("records") if not only_in_first.empty else []
        )
        only_in_second_list = (
            only_in_second.to_dict("records") if not only_in_second.empty else []
        )

        return {
            "only_in_first": only_in_first_list,
            "only_in_second": only_in_second_list,
            "common_ids": common_ids,
            "stats": {
                "count_only_in_first": len(only_in_first_list),
                "count_only_in_second": len(only_in_second_list),
                "count_common": len(common_ids),
            },
        }

    def insert_page(self):
        if self.verify_page_is_valid():
            formated_page = self.format_page()
            formated_page_array_df = pd.DataFrame(formated_page)
            cc_report_by_id_and_type_df = df_query_by_params(
                self.cc_id_reference, self.type
            )
            data_comparation = self.compare_dfs_to_dict(
                formated_page_array_df, cc_report_by_id_and_type_df, "ID"
            )
            only_in_api = data_comparation.get("only_in_first")
            only_in_db = data_comparation.get("only_in_second")
            for reg in only_in_api:
                print(f"Inserido o registro  {reg}")
                create_relatorio_cc(reg)
            for reg in only_in_db:
                print(f"Deletando o registro {reg}")
                reg_id = reg.get("ID")
                self.delete_cc_report_reg_by_id(reg_id)
                print("Must delete")
        Update_running_status(self.cc_id_reference, self.type)
