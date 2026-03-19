import hashlib
import json
import os
import re
from datetime import datetime
import pandas as pd

from manageBenefits import EMPLOYERS_MANAGE_BENEFITS
from manageDependents import EMPLOYERS_MANAGE_DEPENDENTS
from models import EmployersData, EmployersDataBenefits, EmployersDataDependents, db


def filter_dataframe_to_dict(df: pd.DataFrame, column_name: str, value_to_match: any) -> list[dict]:
    filtered_df = df[df[column_name] == value_to_match]
    return filtered_df.to_dict(orient='records')



def datetime_to_string(dt: datetime) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y")
    return dt


def string_to_datetime(date_str: str) -> datetime:
    if date_str and isinstance(date_str, str):
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            return None
    return date_str


def generate_hash(input_string):
    hash_object = hashlib.sha256()
    hash_object.update(str(input_string).encode())
    return hash_object.hexdigest()


def parse_float(value: str) -> float:
    if value is None:
        return 0.0
    cleaned_value = re.sub(r"[^\d,\.]", "", str(value))
    if "," in cleaned_value and "." in cleaned_value:
        cleaned_value = cleaned_value.replace(".", "").replace(",", ".")
    elif "," in cleaned_value:
        cleaned_value = cleaned_value.replace(",", ".")
    try:
        return float(cleaned_value)
    except (ValueError, TypeError):
        return 0.0


# --- Real Relational Database Functions ---
def create_employer(data):
    """Creates a new employer record in the relational database."""
    new_employer_data = EmployersData(
        nome_funcionario=data.get("nome_funcionario"),
        rg_funcionario=data.get("rg_funcionario"),
        cpf_funcionario=data.get("cpf_funcionario"),
        matricula_funcionario=data.get("matricula_funcionario"),
        sexo_funcionario=data.get("sexo_funcionario"),
        local_nascimento_funcionario=data.get("local_nascimento_funcionario"),
        orgao_emissor_rg=data.get("orgao_emissor_rg"),
        serie_ctps_funcionario=data.get("serie_ctps_funcionario"),
        cep_funcionario=data.get("cep_funcionario"),
        endereco_funcionario=data.get("endereco_funcionario"),
        numero_funcionario=data.get("numero_funcionario"),
        bairro_funcionario=data.get("bairro_funcionario"),
        cidade_funcionario=data.get("cidade_funcionario"),
        uf_funcionario=data.get("uf_funcionario"),
        complemento_funcionario=data.get("complemento_funcionario"),
        celular_funcionario=data.get("celular_funcionario"),
        fone_funcionario=data.get("fone_funcionario"),
        email_funcionario=data.get("email_funcionario"),
        nome_pai_funcionario=data.get("nome_pai_funcionario"),
        nome_mae_funcionario=data.get("nome_mae_funcionario"),
        observacoes_funcionario=data.get("observacoes_funcionario"),
        pis_funcionario=data.get("pis_funcionario"),
        ctps_funcionario=data.get("ctps_funcionario"),
        uf_ctps_funcionario=data.get("uf_ctps_funcionario"),
        banco_funcionario=data.get("banco_funcionario"),
        agencia_funcionario=data.get("agencia_funcionario"),
        conta_funcionario=data.get("conta_funcionario"),
        cargo_funcionario=data.get("cargo_funcionario"),
        cbo_funcionario=data.get("cbo_funcionario"),
        departamento_funcionario=data.get("departamento_funcionario"),
        trabalho_inicio=data.get("trabalho_inicio"),
        trabalho_termino=data.get("trabalho_termino"),
        intervalo_inicio=data.get("intervalo_inicio"),
        intervalo_termino=data.get("intervalo_termino"),
        salario_funcionario=data.get("salario_funcionario"),
        status_funcionario=data.get("status_funcionario"),
        data_admissao_funcionario=data.get("data_admissao_funcionario"),
        data_nascimento_funcionario=data.get("data_nascimento_funcionario"),
        id_funcionario=data.get("id_funcionario"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(new_employer_data)
    db.session.commit()
    print(
        f"✅ Successfully CREATED employer '{data.get('nome_funcionario')}' in relational DB."
    )


def get_employer_data_by_id(id):
    """Fetches an employer record from the relational database by their ID."""
    return db.session.query(EmployersData).filter_by(id_funcionario=id).first()


def edit_existing_element(id, data_dict, keys_to_update):
    """Updates an existing employer record in the relational database."""
    existing_element = get_employer_data_by_id(id)
    if existing_element is None:
        return None
    for key in keys_to_update:
        if key in data_dict:
            setattr(existing_element, key, data_dict[key])
    existing_element.updated_at = datetime.utcnow()
    db.session.commit()
    print(f"✅ Successfully UPDATED employer with id '{id}' in relational DB.")
    return existing_element


def are_registers_divergent(reg_db_object, reg_api_dict, keys_to_compare):
    """Compares a DB object with a dictionary to find differences."""
    for key in keys_to_compare:
        db_value = getattr(reg_db_object, key, None)
        api_value = reg_api_dict.get(key)
        if isinstance(db_value, datetime) and isinstance(api_value, datetime):
            if db_value.date() != api_value.date():
                print(
                    f"❗️(DIVERGENCE FOUND) DB Date '{db_value.date()}' <-> API Date '{api_value.date()}' for key: '{key}'"
                )
                return True
        elif db_value != api_value:
            print(
                f"❗️(DIVERGENCE FOUND) DB '{db_value}' <-> API '{api_value}' for key: '{key}'"
            )
            return True
    return False

def model_to_dataframe(model):
    """Converts all records from a model to a pandas DataFrame."""
    records = model.query.all()
    if not records:
        return pd.DataFrame()
    
    columns = [c.key for c in model.__mapper__.columns]
    data = [{col: getattr(rec, col) for col in columns} for rec in records]
    
    return pd.DataFrame(data)




class EMPLOYERS_MANAGE_NEW:
    def __init__(self, data):
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else {}
            if not data:
                raise ValueError("Empty list provided")
        self.api_source = data
        self.api_elements = None
        self.db_elements = None
        self.id = data.get("id_funcionario")
        self.nome_funcionario = data.get("nome_funcionario")
        self.benefits = data.get("beneficios", [])
        self.dependents = data.get("dependentes", [])
        self.previous_employers_data = model_to_dataframe(EmployersData)
        self.current_api_data_ids =[]
        self.employer_general_benefits = model_to_dataframe(EmployersDataBenefits)
        self.employer_general_dependents = model_to_dataframe(EmployersDataDependents)
        
    @staticmethod
    def delete_benefit_register_by_id(id):
        entry_to_delete = db.session.query(EmployersDataBenefits).filter_by(benefit_id=id).first()

        if entry_to_delete:
            db.session.delete(entry_to_delete)
            db.session.commit()
            return True
        else:
            return False


    @staticmethod
    def delete_dependents_register_by_id(id):
        print(f"Delete dependent register with id {id}")
        entry_to_delete = db.session.query(EmployersDataDependents).filter_by(dependents_id=id).first()

        if entry_to_delete:
            db.session.delete(entry_to_delete)
            db.session.commit()
            return True
        else:
            return False

    def verify_elements(self):
        """Prepares the data dictionary, converting dates to datetime objects for the DB."""
        register = self.api_source
        self.api_elements = {
            "nome_funcionario": register.get("nome_funcionario"),
            "rg_funcionario": register.get("rg_funcionario"),
            "cpf_funcionario": register.get("cpf_funcionario"),
            "matricula_funcionario": register.get("matricula_funcionario"),
            "sexo_funcionario": register.get("sexo_funcionario"),
            "local_nascimento_funcionario": register.get(
                "local_nascimento_funcionario"
            ),
            "orgao_emissor_rg": register.get("orgao_emissor_rg"),
            "serie_ctps_funcionario": register.get("serie_ctps_funcionario"),
            "cep_funcionario": register.get("cep_funcionario"),
            "endereco_funcionario": register.get("endereco_funcionario"),
            "numero_funcionario": register.get("numero_funcionario"),
            "bairro_funcionario": register.get("bairro_funcionario"),
            "cidade_funcionario": register.get("cidade_funcionario"),
            "uf_funcionario": register.get("uf_funcionario"),
            "complemento_funcionario": register.get("complemento_funcionario"),
            "celular_funcionario": register.get("celular_funcionario"),
            "fone_funcionario": register.get("fone_funcionario"),
            "email_funcionario": register.get("email_funcionario"),
            "nome_pai_funcionario": register.get("nome_pai_funcionario"),
            "nome_mae_funcionario": register.get("nome_mae_funcionario"),
            "observacoes_funcionario": register.get("observacoes_funcionario"),
            "pis_funcionario": register.get("pis_funcionario"),
            "ctps_funcionario": register.get("ctps_funcionario"),
            "uf_ctps_funcionario": register.get("uf_ctps_funcionario"),
            "banco_funcionario": register.get("banco_funcionario"),
            "agencia_funcionario": register.get("agencia_funcionario"),
            "conta_funcionario": register.get("conta_funcionario"),
            "cargo_funcionario": register.get("cargo_funcionario"),
            "cbo_funcionario": register.get("cbo_funcionario"),
            "departamento_funcionario": register.get("departamento_funcionario"),
            "trabalho_inicio": register.get("trabalho_inicio"),
            "trabalho_termino": register.get("trabalho_termino"),
            "intervalo_inicio": register.get("intervalo_inicio"),
            "intervalo_termino": register.get("intervalo_termino"),
            "salario_funcionario": register.get("salario_funcionario"),
            "status_funcionario": register.get("status_funcionario"),
            "data_admissao_funcionario": string_to_datetime(
                register.get("data_admissao_funcionario")
            ),
            "data_nascimento_funcionario": string_to_datetime(
                register.get("data_nascimento_funcionario")
            ),
            "id_funcionario": register.get("id_funcionario"),
        }

    def verify_elements_bd(self):
        """Fetches the SQLAlchemy object from the relational database."""
        self.db_elements = get_employer_data_by_id(self.id)

    def save_as_key_value_json(self, file_path: str = "employers.json"):
        """Saves data to a key-value JSON file silently."""
        if not self.api_elements:
            return

        matricula = self.api_elements.get("matricula_funcionario")
        if not matricula:
            return

        json_data = self.api_elements.copy()
        json_data["data_admissao_funcionario"] = datetime_to_string(
            json_data["data_admissao_funcionario"]
        )
        json_data["data_nascimento_funcionario"] = datetime_to_string(
            json_data["data_nascimento_funcionario"]
        )

        all_data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                all_data = {}

        all_data[str(matricula)] = json_data

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=4, ensure_ascii=False)
        except IOError:
            pass

    def get_updates(self):
        # print(f"\nProcessing employee: {self.nome_funcionario} (ID: {self.id})")

        self.verify_elements()
        if not self.api_elements or not self.id:
            print("Sem registro")
            return
        self.verify_elements_bd()
        dependents_api_current_array = []
        for dependent in self.dependents:
            dependent_name = dependent.get("nome_dependente")
            dependent_id_string = f"{self.id}-{dependent_name}"
            dependent_ref = {
                "dependents_id": generate_hash(dependent_id_string),
                "id_funcionario": self.id,
                "nome_funcionario": self.nome_funcionario,
                "nome_dependente": dependent_name,
                "tipo_dependente": dependent.get("tipo_dependente"),
                "fone_dependente": dependent.get("fone_dependente"),
                "rg": dependent.get("rg"),
                "cpf": dependent.get("cpf"),
                "data_nascimento": dependent.get("data_nascimento_dependente"),
            }
            dependents_api_current_array.append(dependent_ref.get("dependents_id"))
            employer_manage_dependents = EMPLOYERS_MANAGE_DEPENDENTS(dependent_ref)
            employer_manage_dependents.get_updates()
            
        db_dependent_entries = filter_dataframe_to_dict(self.employer_general_dependents,"nome_funcionario",self.nome_funcionario)    
        ids_list_dependent = [d['dependents_id'] for d in db_dependent_entries]
        only_in_api_dependents = list(set(ids_list_dependent) - set(dependents_api_current_array))
        for id_reg in only_in_api_dependents:
            self.delete_dependents_register_by_id(id_reg)
            
        benefit_api_current_array = []        
        for benefit in self.benefits:
            # print(f"\n Benefit {benefit}")
            benefit_name = benefit.get("nome_beneficio")
            benefit_id_string = f"{self.id}-{benefit_name}"
            benefit_ref = {
                "benefit_id": generate_hash(benefit_id_string),
                "id_funcionario": self.id,
                "nome_funcionario": self.nome_funcionario,
                "nome": benefit_name,
                "valor": parse_float(benefit.get("valor_beneficio")),
            }
            benefit_api_current_array.append(benefit_ref.get("benefit_id"))
            if(benefit_name != None):
                employer_manage_benefit = EMPLOYERS_MANAGE_BENEFITS(benefit_ref)
                employer_manage_benefit.get_updates()
        db_benefit_entries = filter_dataframe_to_dict(self.employer_general_benefits,"nome_funcionario",self.nome_funcionario)    
        ids_list_benefit = [d['benefit_id'] for d in db_benefit_entries]
        only_in_api_benefits = list(set(ids_list_benefit) - set(benefit_api_current_array))
        for id_reg in only_in_api_benefits:
            print("delete this outdated ou delete benefit")
            self.delete_benefit_register_by_id(id_reg)
        
        if self.db_elements is None:
            create_employer(self.api_elements)
        else:
            keys_to_compare = [
                k
                for k in self.api_elements.keys()
                if k not in ["created_at", "updated_at"]
            ]
            if are_registers_divergent(
                self.db_elements, self.api_elements, keys_to_compare
            ):
                edit_existing_element(self.id, self.api_elements, keys_to_compare)
            else:
                print("ℹ️ No divergences found. Relational database is up-to-date.")
