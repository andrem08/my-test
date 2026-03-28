from datetime import datetime

import pandas as pd

from models import CentroCustos, Client, Client_by_CC, OrdersManage, db
from utils.api_to_json_manager import save_object_to_json_file


def create_client_by_cc(data):
    # print(f"Calling for create client {data}", flush=True)
    new_relatorio = Client_by_CC(
        CC=data["CC"],
        id_cc=data["id_cc"],
        id_cliente=data["id_cliente"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_relatorio)
    db.session.commit()


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def get_client_by_cc_by_id(id):
    query = db.session.query(Client_by_CC).filter_by(CC=id).first()
    print(f"Or ref  of client by cc ref here {query}", flush=True)
    return query


def get_cc_by_id(id):
    return db.session.query(CentroCustos).filter_by(CC=id).first()


def edit_existing_cc_by_client(data_dict):
    # Get the existing ClockUser instance from the database
    client_by_cc_id = data_dict.get("CC")
    client_by_cc = get_client_by_cc_by_id(client_by_cc_id)
    print("\n \n Getting or client by cc ref here {client_by_cc}")
    # If the user doesn't exist, you might want to handle that case accordingly
    if client_by_cc is None:
        # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
        return None
    if "id_cc" in data_dict:
        client_by_cc.CC = data_dict["id_cc"]
    if "id_cliente" in data_dict:
        client_by_cc.CC = data_dict["id_cliente"]
    if "ref_cc" in data_dict:
        client_by_cc.CC = data_dict["ref_cc"]

    # Update the 'updated_at' property
    client_by_cc.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.session.commit()

    return client_by_cc


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    # print(f" \n Registro do banco de dados {reg_db}", flush = True)
    # print(f" \n Registro da api {reg_api}", flush = True)
    for key in keys_to_compare:
        print(f"REG DB {reg_db}")
        print(f"REG API {reg_api}")
        if reg_db[key] != reg_api[key]:
            print(f"\n \n The key {key} are divergent", flush=True)
            print("\n \n DB", reg_db[key], flush=True)
            print("\n \n OUTSIDER", reg_api[key], flush=True)
            return True
    return False


class CLIENT_BY_CC_MANAGER:
    def __init__(self):
        self.all = []
        self.client_by_cc_model = model_to_dataframe(Client_by_CC)
        self.centro_custo_model = model_to_dataframe(CentroCustos)
        self.orders_manage_model = model_to_dataframe(OrdersManage)
        self.client_model = model_to_dataframe(Client)
        self.client_by_cc_core = []
        self.cc_core = []

    # def verify_client_by_cc_id(self, id):
    #     # Convert column values and search term to lowercase for case-insensitive comparison
    #     df = self.client_by_cc_model
    #     result_df = df[df["CC"] == id]

    #     if not result_df.empty:
    #         # If there are multiple matches, you may need to decide how to handle them
    #         return True
    #     return False

    def format_client_by_cc_core(self, reg):
        ref = {
            "CC": reg.get("CC"),
            "id_cc": reg.get("id_cc"),
            "ref_cc": reg.get("ref_cc"),
            "id_cliente": reg.get("id_cliente"),
            "ref": "client_by_cc_db",
        }
        self.client_by_cc_core.append(ref)
        self.all.append(ref)

    def format_cc_core(self, reg):
        ref = {
            "CC": reg.get("ref_centro_custos"),
            "id_cc": reg.get("id_centro_custos"),
            "ref_cc": reg.get("desc_centro_custos"),
            "lixeira": reg.get("lixeira"),
            "id_cliente": reg.get("id_cliente"),
            "ref": "cc_db",
        }
        self.cc_core.append(ref)
        self.all.append(ref)
        # Em ordem, pegar client_by cc (pode ser em um df mesmo)

    def cc_by_client_by_cc_id(self, id):
        # Convert column values and search term to lowercase for case-insensitive comparison
        df = self.client_by_cc_model
        result_df = df[df["id_cc"] == id]

        if not result_df.empty:
            # If there are multiple matches, you may need to decide how to handle them
            desired_value = result_df.iloc[0]
            return desired_value
        else:
            print("No matching rows found.")
            return None

    def verify_client_by_id(self, id):
        # Convert column values and search term to lowercase for case-insensitive comparison
        df = self.client_model
        result_df = df[df["id_cliente"] == id]

        if not result_df.empty:
            # If there are multiple matches, you may need to decide how to handle them
            desired_value = result_df.iloc[0].id_cliente
            return desired_value
        else:
            print("No matching rows found.")
            return "-1"

    def client_by_cc_label(self, cc):
        # Convert column values and search term to lowercase for case-insensitive comparison
        df = self.orders_manage_model
        result_df = df[df["ref_cc"] == cc]

        if not result_df.empty:
            # If there are multiple matches, you may need to decide how to handle them
            desired_value = result_df.iloc[0].id_cliente
            return self.verify_client_by_id(desired_value)
        else:
            print("No matching rows found.")
            return "-1"

    def create_client_by_cc(self, data):
        client_by_cc_reg = Client_by_CC(
            CC=data["CC"],
            id_cc=data["id_cc"],
            id_cliente=self.client_by_cc_label(data["CC"]),
            ref_cc=data["ref_cc"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(client_by_cc_reg)
        db.session.commit()

    # Verificar se todos cc existem em client_by cc

    def edit_client_by_cc_client_id(self, id, data_dict):
        # Get the existing ClockUser instance from the database
        reg = get_client_by_cc_by_id(id)

        print(
            f"\n \n \n Getting data to edit this element id : {id} data_dict :{data_dict}"
        )
        print(f" \n \n Reg reference here {reg}")
        # If the user doesn't exist, you might want to handle that case accordingly
        if reg is None:
            # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
            return None

        reg.id_cliente = self.client_by_cc_label(data_dict["CC"])
        # Update the 'updated_at' property
        reg.updated_at = datetime.utcnow()

        # Commit the changes to the database
        db.session.commit()

        return reg

    def edit_client_by_cc(self, id, data_dict):
   
        reg = get_client_by_cc_by_id(id)
        print(f"Reg is called here {reg}", flush=True)
        print(f"Relative data dict {data_dict}", flush=True)
        # If the user doesn't exist, you might want to handle that case accordingly
        if reg is None:
            # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
            return None

        # Update the instance based on data_dict
        if "id_cc" in data_dict:
            reg.id_cc = data_dict["id_cc"]
        if "ref_cc" in data_dict:
            reg.ref_cc = data_dict["ref_cc"]
        client_ref = self.client_by_cc_label(data_dict["CC"])
        reg.id_cliente = self.client_by_cc_label(data_dict["CC"])
        print(f"Cliente ref here  {client_ref}", flush=True)
        # Update the 'updated_at' property
        reg.updated_at = datetime.utcnow()

        # Commit the changes to the database
        db.session.commit()

        return reg

    def delete_cliente_by_cc(self, id):
        entry_to_delete = db.session.query(Client_by_CC).filter_by(id_cc=id).first()

        if entry_to_delete:
            db.session.delete(entry_to_delete)
            db.session.commit()
            return True
        else:
            return False

    def corner_cases_of_cc_by_client(self, CC_REF):
        cases = [
            "AT-AMS",
            "AT-DAM",
            "AT-GER",
            "AT-JSD",
            "RT-IMP",
            "NO-SET",
            "RT-ADM",
            "RT-AMS",
            "RT-DAM",
            "RT-ETQ",
            "RT-FAB",
            "RT-JSD",
            "RT-RCC",
            "RT-REF",
            "RT-RHT",
            "RT-COM",
            "RT-ATT",
            "RT-ENG",
            "NO-SET",
        ]
        if CC_REF in cases:
            print(f"O elemento {CC_REF} é um corner case", flush=True)
            return True
        return False

    def update_cc_by_id(self):
        # Rodando uma rotina para preecher todos os casos falhos

        list_cc = self.centro_custo_model.to_dict(orient="records")
        list_client_by_cc = self.client_by_cc_model.to_dict(orient="records")
        for reg in list_cc:
            # print(f"Or reg here {reg}", flush=True)
            self.format_cc_core(reg)
        for reg in list_client_by_cc:
            # print(f"Or reg here client by cc  {reg}", flush=True)
            self.format_client_by_cc_core(reg)

        grouped_arrays = group_elements_by_key(self.all, "id_cc")
        for group in grouped_arrays:
            size = len(group)
            if size == 1:
              
                ref = group[0].get("ref")
                CC = group[0].get("CC")
                print(f" \n \n \n Or group to create here {group} \n \n ")
                if ref == "cc_db":
                    lixeira = group[0].get("lixeira")
                    # Verificar se a label é nova ou se já existe
                    print(f"Or ref stay here {group[0]}", flush=True)
                    id_cc = group[0].get("id_cc")
                    if lixeira != "Sim":
                        if get_client_by_cc_by_id(CC) is None:
                            # Não temos ainda, vamos criar
                            print(
                                " \n \n \n \n Chamou na hora de criar  \n \n \n ",
                                flush=True,
                            )
                            self.create_client_by_cc(group[0])
                        else:
                            # Achar o campo é editar ele
                            self.edit_client_by_cc(CC, group[0])
                    else:
                        self.delete_cliente_by_cc(id_cc)

            if size == 2:
                ref = group[0].get("ref")
                lixeira = group[0].get("lixeira")
                id_cc = group[0].get("id_cc")
                id_client = group[1].get("id_cliente")
                if lixeira != "Sim":
                    CC = group[0].get("CC")

                    ref_keys = ["id_cc", "ref_cc"]
                    if self.corner_cases_of_cc_by_client(CC) is False:
                        if are_registers_divergent(group[0], group[1], ref_keys):
                            # Editamos aqui
                            self.edit_client_by_cc(CC, group[1])
                else:
                    self.delete_cliente_by_cc(id_cc)

                if id_client == "-1":
                    CC = group[1].get("CC")
                    # print(f" \n \n Nosso cliente esta como -1 {id_client} {group[1]}", flush = True)
                    self.edit_client_by_cc_client_id(CC, group[1])
        return {
            "message": "REF BY CC UPDATED",
            # "client_by_cc_core": self.client_by_cc_core,
            # "cc_core": self.cc_core,
            "all": grouped_arrays,
        }
