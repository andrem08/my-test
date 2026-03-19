import json
import os
from datetime import datetime

import pandas as pd

from models import Employers, EmployersData, db


def get_line_by_keyword(df, keyword, value):
    if keyword not in df.columns:
        raise KeyError(f"The column '{keyword}' does not exist in the DataFrame.")

    result_df = df[df[keyword] == value]

    if not result_df.empty:
        desired_row = result_df.iloc[0]

        return desired_row
    else:
        print("No matching rows found.")
        return "-1"


def model_to_dataframe(model):

    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def create_employer(data):
    new_employer = Employers(
        vhsys_id=data["vhsys_id"],
        matricula=data["matricula"],
        nome=data["nome"],
        cargo=data["cargo"],
        cbo=data["cbo"],
        rg=data["rg"],
        cpf=data["cpf"],
        data_nascimento=data["data_nascimento"],
        salario=data["salario"],
        data_adm=data["data_adm"],
        data_dem=data["data_dem"],
        status=data["status"],
        data_cad=data["data_cad"],
        data_mod=data["data_mod"],
        depto=data["depto"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(new_employer)
    db.session.commit()


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


def get_element_by_id(id):
    return db.session.query(Employers).filter_by(vhsys_id=id).first()


def disable_user_by_vhsys_id(vhsys_id):
    existing_element = get_element_by_id(id)

    if existing_element is None:
        return None

    existing_element.status = "Inativo"
    existing_element.updated_at = datetime.utcnow()
    db.session.commit()

    return existing_element


def edit_existing_element(id, data_dict, keys_to_update):
    existing_element = get_element_by_id(id)

    if existing_element is None:
        return None

    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_element, key, data_dict[key])

    existing_element.updated_at = datetime.utcnow()
    db.session.commit()

    return existing_element


def are_registers_divergent(reg_db, reg_api, keys_to_compare):
    for key in keys_to_compare:
        if reg_db[key] != reg_api[key]:
            print(
                f"(DIVERGENCES) DB {reg_db[key]} <-> API {reg_api[key]} ,({key})",
                flush=True,
            )
            return True
    return False


def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def save_to_json(data, file_path):
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, default=datetime_serializer)


class EMPLOYERS_MANAGE:
    def __init__(self, data):
        self.new = []
        self.api_source = data
        self.api_elements = []
        self.db_elements = []
        self.all = []

    def create_insertion_log(self, table, note):
        return {"env": os.getenv("CONTEXT"), "table": table, "note": note}

    # def format_birth_date(self, date):

    def verify_elements(self):
        registers = self.api_source

        for register in registers:
            register_dict = {
                "vhsys_id": int(register["ID"]),
                "matricula": int(register["Matricula"]),
                "nome": register["Nome"],
                "cargo": register["Cargo"],
                "cbo": register["CBO"],
                "rg": register["Rg"],
                "cpf": register["CPF"],
                "data_nascimento": self.parse_timestamp(register["DataNascimento"]),
                "salario": float(register["Salario"]),
                "data_adm": self.parse_timestamp(register["DataAdmissao"]),
                "data_dem": self.parse_timestamp(register["DataDemissao"]),
                "status": register["Status"],
                "data_cad": self.parse_timestamp(register["DataCad"]),
                "data_mod": self.parse_timestamp(register["DataMod"]),
                "depto": register["Depto"],
                "source": "api",
            }
            self.api_elements.append(register_dict)
            self.all.append(register_dict)

    def parse_timestamp(self, timestamp):
        """
        Helper method to convert a timestamp to a datetime object.
        Returns None if the timestamp is empty or invalid.
        """
        try:
            return datetime.fromtimestamp(int(timestamp))
        except (ValueError, TypeError):
            return None

    def verify_elements_bd(self):
        registers_db = Employers.query.all()
        for register in registers_db:
            register_dict = {
                # "id_employers": register.id_employers,
                "vhsys_id": register.vhsys_id,
                "matricula": register.matricula,
                "nome": register.nome,
                "cargo": register.cargo,
                "cbo": register.cbo,
                "rg": register.rg,
                "cpf": register.cpf,
                "data_nascimento": register.data_nascimento,
                "salario": register.salario,
                "data_adm": register.data_adm,
                "data_dem": register.data_dem,
                "status": register.status,
                "data_cad": register.data_cad,
                "data_mod": register.data_mod,
                "depto": register.depto,
                "source": "db",
            }
            self.db_elements.append(register_dict)
            self.all.append(register_dict)

    def get_updates(self):
        self.verify_elements()
        self.verify_elements_bd()
        keys_array = [
            "vhsys_id",
            "matricula",
            "nome",
            "cargo",
            "cbo",
            "rg",
            "cpf",
            "data_nascimento",
            "salario",
            "data_adm",
            "data_dem",
            "status",
            "data_cad",
            "data_mod",
            "depto",
        ]
        grouped_arrays = group_elements_by_key(self.all, "vhsys_id")

        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    try:
                        create_employer(group[0])
                    except Exception as e:
                        print(f"An error occurred: {e}")
                else:
                    print(f"Elemento só existe no banco {group[0]}", flush=True)
                    # Nesse caso, o  funcionario já não esta mais ativo
                    element_id = group[0].get("vhsys_id")

            if len(group) == 2:
                if are_registers_divergent(group[0], group[1], keys_array):
                    try:
                        edit_existing_element(
                            group[0].get("vhsys_id"), group[0], keys_array
                        )
                    except Exception as e:
                        print(f"An error occurred: {e}")
        return {"message": "Employers data updated"}

    def fill_auxilar_tables(self):
        print("\n \n \n Fill auxilar elements")
        employers_df = model_to_dataframe(Employers)
        employers_data_df = model_to_dataframe(EmployersData)
        employers_subs = employers_df["matricula"].tolist()
        for emp_sub in employers_subs:
            print(f"\n EMP_SUB {emp_sub}")
            # Comparando os dois casos
            line_employers = get_line_by_keyword(employers_df, "matricula", emp_sub)
            line_employers_data = get_line_by_keyword(
                employers_data_df, "matricula_funcionario", str(emp_sub)
            )
            # print(
            #     f"STATUS COMPARE ({line_employers['status']}) - ({line_employers_data['status_funcionario']})"
            # )
            # print(f"Line employers {line_employers}")
            # print(f"Line employers data {line_employers_data}")
            if line_employers.get("status") != line_employers_data.get(
                "status_funcionario"
            ):
                # Vamos editar isso no status_funcionario
                existing_element = (
                    db.session.query(EmployersData)
                    .filter_by(matricula_funcionario=(str(emp_sub)))
                    .first()
                )
                existing_element.status_funcionario = line_employers["status"]
                print("edit : existing_element", existing_element)
                db.session.commit()
