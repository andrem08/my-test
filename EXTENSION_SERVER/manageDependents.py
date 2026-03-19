import json
import os
from datetime import datetime
from models import EmployersDataDependents, db

def datetime_to_string(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y")

def string_to_datetime(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%d/%m/%Y")

def create_dependent_data(data):
    new_employer_data = EmployersDataDependents(
        dependents_id=data["dependents_id"],
        id_funcionario=data["id_funcionario"],
        nome_funcionario=data["nome_funcionario"],
        nome_dependente=data["nome_dependente"],
        tipo_dependente=data["tipo_dependente"],
        fone_dependente=data["fone_dependente"],
        rg=data["rg"],
        cpf=data["cpf"],
        data_nascimento=data["data_nascimento"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(new_employer_data)
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


def get_employer_data_by_id(id):
    return db.session.query(EmployersDataDependents).filter_by(dependents_id=id).first()


def edit_existing_element(id, data_dict, keys_to_update):
    existing_element = get_employer_data_by_id(id)

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

class EMPLOYERS_MANAGE_DEPENDENTS:
    def __init__(self, data):
        self.api_source = data
        self.api_elements = None
        self.db_elements = None
        self.id = data.get("dependents_id")

    def create_insertion_log(self, table, note):
        return {"env": os.getenv("CONTEXT"), "table": table, "note": note}

    def verify_elements(self):
        register = self.api_source
        register_dict = {
            "dependents_id": register["dependents_id"],
            "id_funcionario": register["id_funcionario"],
            "nome_funcionario": register["nome_funcionario"],
            "nome_dependente": register["nome_dependente"],
            "tipo_dependente": register["tipo_dependente"],
            "fone_dependente": register["fone_dependente"],
            "rg": register["rg"],
            "cpf": register["cpf"],
            "data_nascimento": string_to_datetime(register["data_nascimento"]),
            "source": "api",
        }
        self.api_elements = register_dict

    def parse_timestamp(self, timestamp):
        try:
            return datetime.fromtimestamp(int(timestamp))
        except (ValueError, TypeError):
            return None

    def verify_elements_bd(self):
        registers_db = get_employer_data_by_id(self.id)
        if registers_db:
            register_dict = {
                "dependents_id": registers_db.dependents_id,
                "id_funcionario": registers_db.id_funcionario,
                "nome_funcionario": registers_db.nome_funcionario,
                "nome_dependente": registers_db.nome_dependente,
                "tipo_dependente": registers_db.tipo_dependente,
                "fone_dependente": registers_db.fone_dependente,
                "rg": registers_db.rg,
                "cpf": registers_db.cpf,
                "data_nascimento": registers_db.data_nascimento,
                "source": "db",
            }
            self.db_elements = register_dict

    def get_updates(self):
        id_employer = self.api_source.get("id_funcionario")
        self.verify_elements()
        self.verify_elements_bd()
        if self.db_elements is None:
            print(f"Nosso registro que deve ser inserido aqui  {self.api_source}")
            print("Não temos registro no banco")
            create_dependent_data(self.api_elements)
        else:
            keys = [
                "id_funcionario",
                "nome_funcionario",
                "nome_dependente",
                "tipo_dependente",
                "fone_dependente",
                "rg",
                "cpf",
                "data_nascimento",
            ]
            is_divergent = are_registers_divergent(
                self.db_elements, self.api_elements, keys_to_compare=keys
            )
            if is_divergent:
                edit_existing_element(self.id, self.api_elements, keys)
