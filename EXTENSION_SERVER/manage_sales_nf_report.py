from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

import pytz

from cost_center_manager import COST_CENTER_MANAGER
from models import SalesNFReport, db
from update_extension_manager import UPDATE_EXTENSION_STATUS


def parse_decimal(value, precision=None) -> Decimal:
    if isinstance(value, Decimal):
        if precision is not None:
            quantizer = Decimal("1e-" + str(precision))
            return value.quantize(quantizer, rounding=ROUND_HALF_UP)
        return value
    if value is None or value == "":
        return Decimal("0.0")
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


def timestamp_to_brazil_time(timestamp) -> str:
    if not timestamp:
        return ""
    brt_tz = pytz.timezone("America/Sao_Paulo")
    dt_object = datetime.fromtimestamp(int(timestamp), brt_tz)
    return dt_object.strftime("%d/%m/%Y %H:%M:%S")


def create_sales_nf_report_item(data):
    for key, value in data.items():
        if isinstance(value, Decimal):
            data[key] = str(value)
    new_regular_bills = SalesNFReport(**data)
    db.session.add(new_regular_bills)
    db.session.commit()


def get_element_by_nota(nota):
    return db.session.query(SalesNFReport).filter_by(Nota=nota).first()


def edit_existing_element(nota, data_dict, keys_to_update):
    existing_element = get_element_by_nota(nota)
    if existing_element is None:
        print(f"Could not find element with Nota {nota} during update attempt.")
        return None
    for key in keys_to_update:
        if key in data_dict:
            value = data_dict[key]
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
        # Ensure values are strings for comparison to avoid type mismatches
        if str(val_db) != str(val_api):
            print(
                f"(DIVERGENCE) Key: '{key}' -> DB: {val_db} <-> API: {val_api}",
                flush=True,
            )
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


class SALES_NF_REPORT_MANAGE:
    def __init__(self, data):
        self.api_source = data
        self.all = []
        self.processed_api_notas = set()
        self.update_report_status = UPDATE_EXTENSION_STATUS("SALES_NF")
        self.update_report_status.update_run_status(1)

    def verify_elements(self):
        registers = self.api_source
        CC_MANAGER = COST_CENTER_MANAGER()
        for register in registers:
            try:
                # FIX 2: Treat Nota as a string to match the corrected model
                nota_str = str(register["Nota"]).strip()
                if not nota_str:  # Skip if Nota is an empty string
                    continue

                if nota_str in self.processed_api_notas:
                    print(f"Skipping duplicate API record with Nota: {nota_str}")
                    continue
                self.processed_api_notas.add(nota_str)

                register_dict = {
                    "ID": register["ID"],
                    "Nota": nota_str,
                    "Cliente": register["Cliente"],
                    "ValorProdutos": parse_decimal(
                        register["ValorProdutos"], precision=2
                    ),
                    "ValorDesconto": parse_decimal(
                        register["ValorDesconto"], precision=2
                    ),
                    "ValorFrete": parse_decimal(register["ValorFrete"], precision=2),
                    "ValorTotal": parse_decimal(register["ValorTotal"], precision=2),
                    "ValorICMS": parse_decimal(register["ValorICMS"], precision=2),
                    "ValorIPI": parse_decimal(register["ValorIPI"], precision=2),
                    "ValorST": parse_decimal(register["ValorST"], precision=2),
                    "PesoBruto": parse_decimal(register["PesoBruto"], precision=2),
                    "PesoLiquido": parse_decimal(register["PesoLiquido"], precision=2),
                    "DataPedido": timestamp_to_brazil_time(register["DataPedido"]),
                    "DataEmissao": timestamp_to_brazil_time(register["DataEmissao"]),
                    "DataAutorizacao": timestamp_to_brazil_time(
                        register["DataAutorizacao"]
                    ),
                    "DataCad": timestamp_to_brazil_time(register["DataCad"]),
                    "DataMod": timestamp_to_brazil_time(register["DataMod"]),
                    "DataCancelamento": timestamp_to_brazil_time(
                        register["DataCancelamento"]
                    ),
                    "cc_ref": str(
                        CC_MANAGER.get_cc_label(register.get("ObservacoesInternas"))
                    ),
                    "source": "api",
                }

                for key in register:
                    if key not in register_dict:
                        register_dict[key] = register[key]

                self.all.append(register_dict)

            except (ValueError, TypeError, KeyError) as e:
                print(
                    f"Skipping record due to invalid or missing 'Nota': {register.get('Nota')}. Error: {e}"
                )

    def verify_elements_bd(self):
        registers_db = SalesNFReport.query.all()
        for register in registers_db:
            register_dict = {
                c.name: getattr(register, c.name) for c in register.__table__.columns
            }

            # All fields from the DB are text, so we parse them into Decimals for comparison
            register_dict["ValorProdutos"] = parse_decimal(
                register.ValorProdutos, precision=2
            )
            register_dict["ValorDesconto"] = parse_decimal(
                register.ValorDesconto, precision=2
            )
            register_dict["ValorFrete"] = parse_decimal(
                register.ValorFrete, precision=2
            )
            register_dict["ValorTotal"] = parse_decimal(
                register.ValorTotal, precision=2
            )
            register_dict["ValorICMS"] = parse_decimal(register.ValorICMS, precision=2)
            register_dict["ValorIPI"] = parse_decimal(register.ValorIPI, precision=2)
            register_dict["ValorST"] = parse_decimal(register.ValorST, precision=2)
            register_dict["PesoBruto"] = parse_decimal(register.PesoBruto, precision=2)
            register_dict["PesoLiquido"] = parse_decimal(
                register.PesoLiquido, precision=2
            )

            register_dict["source"] = "db"
            self.all.append(register_dict)

    def get_updates(self):
        print("Iniciando SALES NF REPORT MANAGER")
        self.verify_elements()
        self.verify_elements_bd()

        # The primary key 'Nota' should not be in the list of keys to compare for updates
        keys_to_compare = [
            c.name
            for c in SalesNFReport.__table__.columns
            if c.name not in ["Nota", "created_at", "updated_at"]
        ]

        grouped_arrays = group_elements_by_key(self.all, "Nota")

        for group in grouped_arrays:
            if len(group) == 1:
                if group[0].get("source") == "api":
                    # FIX 3: Simplified the error handling back to a simple try/except
                    try:
                        print(f"Creating new record with Nota: {group[0].get('Nota')}")
                        data_to_create = group[0].copy()
                        data_to_create.pop("source", None)
                        data_to_create.pop("RazaoSocial", None)
                        data_to_create["created_at"] = datetime.now()
                        data_to_create["updated_at"] = datetime.now()
                        create_sales_nf_report_item(data_to_create)
                    except Exception as e:
                        db.session.rollback()
                        self.update_report_status.update_run_status(-1)
                        print(
                            f"An error occurred while creating Nota {group[0].get('Nota')}: {e}"
                        )

            elif len(group) == 2:
                api_reg = group[0] if group[0]["source"] == "api" else group[1]
                db_reg = group[0] if group[0]["source"] == "db" else group[1]

                if are_registers_divergent(db_reg, api_reg, keys_to_compare):
                    try:
                        print(
                            f"Updating existing record with Nota: {api_reg.get('Nota')}"
                        )
                        edit_existing_element(
                            api_reg.get("Nota"), api_reg, keys_to_compare
                        )
                    except Exception as e:
                        db.session.rollback()
                        self.update_report_status.update_run_status(-1)
                        print(
                            f"An error occurred while editing Nota {api_reg.get('Nota')}: {e}"
                        )

        self.update_report_status.update_run_status(2)
        print("Finalizando SALES NF REPORT MANAGER")
        return {"message": "Manage sales nf report updated"}
