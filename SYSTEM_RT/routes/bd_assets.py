import re
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request
from sqlalchemy.orm import class_mapper

from models import (
    CentroCustos,
    Client,
    Client_by_CC,
    Colaborador_cargo_value,
    Indice_ano,
    Pedido,
    PrimaData,
    ServiceOrder,
    User_by_name,
    Valor_base_by_cargo,
    db,
)

bd_assets_route = Blueprint("BD_ASSETS", __name__)

load_dotenv()


def create_user_by_name(data):
    print(f"Calling for create client {data}", flush=True)
    new_user_by_name = User_by_name(
        user=data["user"],
        user_name=data["user_name"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_user_by_name)
    db.session.commit()


def create_index_by_year(data):
    print(f"Calling for create client {data}", flush=True)
    new_index_by_year = Indice_ano(
        id_ano=data["ano"],
        indice=data["fator"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_index_by_year)
    db.session.commit()


def get_id_by_cargo(cargo_value):
    print(f"Calling get_id_by_cargo for cargo: {cargo_value}", flush=True)

    # Assuming 'db' is an instance of Flask-SQLAlchemy
    existing_row = Valor_base_by_cargo.query.filter(
        db.func.lower(Valor_base_by_cargo.cargo) == cargo_value.lower().strip()
    ).first()

    if existing_row:
        return existing_row.id_local
    else:
        # Handle the case where the row with the specified 'cargo' is not found
        return -1


def combine_date_time(date_str, time_str):
    # Convert date string to datetime object
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")

    # Convert time string to datetime object
    time_obj = datetime.strptime(time_str, "%H:%M")

    # Combine date and time
    combined_datetime = datetime(
        date_obj.year, date_obj.month, date_obj.day, time_obj.hour, time_obj.minute
    )

    return combined_datetime


def create_prima_entry(ref):
    new_service_order = PrimaData(
        ID=ref.get("ID"),
        CENTRO_DE_CUSTO=ref.get("CENTRO_DE_CUSTO"),
        PROJETO=ref.get("PROJETO"),
        CLIENTE=ref.get("CLIENTE"),
        DESCRICAO=ref.get("DESCRICAO"),
        TAREFA=ref.get("TAREFA"),
        USUARIO=ref.get("USUARIO"),
        ATIVIDADE=ref.get("ATIVIDADE"),
        DATA_INICIO=ref.get("DATA_INICIO"),
        HORA_INICIO=ref.get("HORA_INICIO"),
        DATA_FINAL=ref.get("DATA_FINAL"),
        HORA_FINAL=ref.get("HORA_FINAL"),
        interval_start_moment=combine_date_time(
            ref.get("DATA_INICIO"), ref.get("HORA_INICIO")
        ),
        interval_end_moment=combine_date_time(
            ref.get("DATA_FINAL"), ref.get("HORA_FINAL")
        ),
        time_difference_in_minutes=ref.get("time_difference_in_minutes"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(new_service_order)
    db.session.commit()


def create_contexted_hour(ref):
    print(f"Ref {ref}")


def create_colaborador_cargo_value(data):
    print(f"Calling create colaborador cargo value  {data}", flush=True)
    categoria = data["categoria"]
    print(f"data [cargo] : {categoria}", flush=True)
    id_cargo = get_id_by_cargo(categoria)
    print(f" id cargo {id_cargo}")

    new_colaborador_by_cargo_value = Colaborador_cargo_value(
        colaborador=data["colaborador"],
        ativo=data["ativo"],
        cargo_id=id_cargo,
        adm_percent=data["adm"],
        momento_inicio_cargo=data["momento_inicio_cargo"],
        momento_fim_cargo=data["momento_fim_cargo"],
        cargo_atual=data["cargo_atual"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_colaborador_by_cargo_value)
    db.session.commit()


def create_valor_base_by_cargo(data):
    print(f"Calling for create client {data}", flush=True)
    new_user_by_name = Valor_base_by_cargo(
        cargo=data["cargo"],
        valor_base=data["valor_base"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_user_by_name)
    db.session.commit()


@bd_assets_route.route("/bd_assets/valor_base_by_cargo/new", methods=["POST"])
def bd_valor_base_by_cargo():
    try:
        data = request.get_json()
        create_valor_base_by_cargo(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Insert new CC report line successfully"}), 201


@bd_assets_route.route("/bd_assets/name_equivalence/new", methods=["POST"])
def bd_name_equivalence():
    try:
        data = request.get_json()
        create_user_by_name(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Insert new CC report line successfully"}), 201


@bd_assets_route.route("/bd_assets/index_year/new", methods=["POST"])
def bd_index_by_year():
    try:
        data = request.get_json()
        create_index_by_year(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Insert new CC report line successfully"}), 201


@bd_assets_route.route("/bd_assets/colaborador_cargo/new", methods=["POST"])
def bd_colaborador_cargo_equivalence():
    try:
        data = request.get_json()
        create_colaborador_cargo_value(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Insert new CC report line successfully"}), 201


@bd_assets_route.route("/prima_entry/new", methods=["POST"])
def bd_prima_entry():
    try:
        data = request.get_json()
        create_prima_entry(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Insert new CC report line successfully"}), 201


@bd_assets_route.route("/prima_entries", methods=["GET"])
def to_prima_csv_route():
    # Get all orders
    all_registers = PrimaData.query.all()

    # Extract column names from the model
    column_names = [column.key for column in PrimaData.__table__.columns]

    # Create a DataFrame from the orders
    all_registers_df = pd.DataFrame(
        [
            {col: getattr(register, col) for col in column_names}
            for register in all_registers
        ]
    )

    # Create a CSV string from the DataFrame
    csv_data = all_registers_df.to_csv(index=False)

    # Create a CSV response
    response = Response(
        csv_data,
        content_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=prima-data.csv",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    return response


def extract_numeric_part(text):
    pattern = re.compile(r"\b(\d{6})\b")
    match = pattern.search(text)

    if match:
        return int(match.group(1))
    else:
        return -1


def create_cost_center(data):
    new_centro = CentroCustos(
        id_centro_custos=data["id_centro_custos"],
        desc_centro_custos=data["desc_centro_custos"],
        status_centro_custos=data["status_centro_custos"],
        data_cad_centro=data["data_cad_centro"],
        lixeira=data["lixeira"],
        ref_centro_custos=data["ref_centro_custos"],
    )

    db.session.add(new_centro)
    db.session.commit()


def client_by_cc(data):
    # Check if a row with the same primary key already exists
    existing_row = Client_by_CC.query.filter_by(CC=data["CC"]).first()
    if existing_row:
        # If a row already exists, modify the existing row
        existing_row.id_cc = data["id_cc"]
        existing_row.id_cliente = data["client_id"]
        existing_row.ref_cc = data["DESC_CC"]
        existing_row.updated_at = datetime.now()
    else:
        # If a row does not exist, add a new row
        new_client_by_cc = Client_by_CC(
            CC=data["CC"],
            id_cc=data["id_cc"],
            id_cliente=data["client_id"],
            ref_cc=data["DESC_CC"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.session.add(new_client_by_cc)

    db.session.commit()


def verify_numeric_int(number):
    if isinstance(number, int):
        return number
    if number.isdigit():
        return int(number)
    return 0.0


def create_client(data):
    print(f"Calling for create client {data}", flush=True)
    new_client = Client(
        id_cliente=verify_numeric_int(data["id_cliente"]),
        id_registro=verify_numeric_int(data["id_registro"]),
        # data_cad_cliente=datetime.now(),
        razao_cliente=data["razao_cliente"],
        fantasia_cliente=data["fantasia_cliente"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(new_client)
    db.session.commit()


def update_cost_center():
    register_dict = {
        "id_centro_custos": "-1",
        "desc_centro_custos": "NO-SET",
        "status_centro_custos": "Ativo",
        "data_cad_centro": datetime.now(),
        "lixeira": "Sim",
        "ref_centro_custos": "NO-SET",
        "cliente": "-1",
    }
    create_cost_center(register_dict)


def update_clients():
    register_dict = {
        "id_cliente": -1,
        "id_registro": -1,
        "razao_cliente": "NO-SET",
        "fantasia_cliente": "NO-SET",
    }
    create_client(register_dict)


@bd_assets_route.route("/tables_defaults", methods=["PUT"])
def add_table_defaults():
    try:
        # update_cost_center()
        update_clients()
    except Exception as e:
        print(f"An error occurred: {e}")

    return "Done"


def model_to_dict(instance):
    return {
        column.key: getattr(instance, column.key)
        for column in class_mapper(instance.__class__).mapped_table.c
    }


def get_objects_by_filters(model, filters):
    query = model.query

    # Apply filters to the query
    if filters:
        query = query.filter_by(**filters)

    # Retrieve objects from the query
    objects = query.all()

    # Transforming the data into a dictionary array
    objects_list = [model_to_dict(obj) for obj in objects]

    return objects_list


def verify_keyword_divergence(line, first_keyword, second_keyord):
    if first_keyword in line:
        return line.get(first_keyword)
    if second_keyord in line:
        return line.get(second_keyord)
    return "-1"


def get_key_word_or_default(line, keyword, default):
    if keyword in line:
        return line.get(keyword)
    return default


def format_output(line, reference):
    print(f"\n Line {line}", flush=True)
    ref = {
        "type": reference,
        "id_pedido": get_key_word_or_default(line, "id_pedido", "*"),
        "id_cliente": get_key_word_or_default(line, "id_cliente", "-1"),
        "centro_de_custo": verify_keyword_divergence(line, "ref_centro_custos", "cc"),
        "nome_cliente": get_key_word_or_default(line, "nome_cliente", "*"),
        "vendedor_pedido": get_key_word_or_default(line, "vendedor_pedido", "*"),
        "valor_total_produtos": get_key_word_or_default(
            line, "valor_total_produtos", "*"
        ),
        "desconto_pedido": get_key_word_or_default(line, "desconto_pedido", "*"),
        "desconto_pedido_porc": get_key_word_or_default(
            line, "desconto_pedido_porc", "*"
        ),
        "peso_total_nota": get_key_word_or_default(line, "peso_total_nota", "*"),
        "peso_total_nota_liq": get_key_word_or_default(
            line, "peso_total_nota_liq", "*"
        ),
        "frete_pedido": get_key_word_or_default(line, "frete_pedido", "*"),
        "referencia_ordem": get_key_word_or_default(line, "referencia_ordem", "*"),
        "valor_baseICMS": get_key_word_or_default(line, "valor_baseICMS", "*"),
        "valor_ICMS": get_key_word_or_default(line, "valor_ICMS", "*"),
        "valor_baseST": get_key_word_or_default(line, "valor_baseST", "*"),
        "valor_ST": get_key_word_or_default(line, "valor_ST", "*"),
        "valor_IPI": get_key_word_or_default(line, "valor_IPI", "*"),
        "condicao_pagamento_id": get_key_word_or_default(
            line, "condicao_pagamento_id", "*"
        ),
        "valor_total_servicos": get_key_word_or_default(
            line, "valor_total_servicos", "*"
        ),
        "valor_total_pecas": get_key_word_or_default(line, "valor_total_pecas", "*"),
        "valor_total_despesas": get_key_word_or_default(
            line, "valor_total_despesas", "*"
        ),
        "valor_total_desconto": get_key_word_or_default(
            line, "valor_total_desconto", "*"
        ),
        "valor_total_os": get_key_word_or_default(line, "valor_total_os", "*"),
        "frete_por_pedido": get_key_word_or_default(line, "frete_por_pedido", "*"),
        "data_pedido": get_key_word_or_default(line, "data_pedido", "*"),
        "prazo_entrega": get_key_word_or_default(line, "prazo_entrega", "*"),
        "referencia_pedido": get_key_word_or_default(line, "referencia_pedido", "*"),
        "obs_pedido": get_key_word_or_default(line, "obs_pedido", "*"),
        "obs_interno_pedido": get_key_word_or_default(line, "obs_interno_pedido", "*"),
        "status_pedido": get_key_word_or_default(line, "status_pedido", "*"),
        "data_cad_pedido": get_key_word_or_default(line, "data_cad_pedido", "*"),
        "data_mod_pedido": get_key_word_or_default(line, "data_mod_pedido", "*"),
        "lixeira": get_key_word_or_default(line, "lixeira", "*"),
        "contas_pedido": get_key_word_or_default(line, "contas_pedido", "*"),
    }
    print("REF ->", ref, flush=True)
    return ref


def remove_non_int_values_for_key(array_of_dicts, target_key):
    for d in array_of_dicts:
        if target_key in d:
            value = d[target_key]
            if not isinstance(value, int):
                del d[target_key]


def get_order_results():
    filter_pedidos = False
    filter_os = False

    pedidos = get_objects_by_filters(Pedido, filter_pedidos)
    service_orders = get_objects_by_filters(ServiceOrder, filter_os)
    result = []

    for pedido in pedidos:
        result.append(format_output(pedido, "OV"))
    for service_order in service_orders:
        result.append(format_output(service_order, "OS"))
    # remove_non_int_values_for_key(result, "centro_de_custo")

    return result


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def get_cc_id(row):
    if row["desc_centro_custos"] == "Administração":
        return "0"
    if row["ref_centro_custos"] != "-1":
        return row["ref_centro_custos"]
    return "-1"


def extract_prefix(text):
    pattern = r"^[A-Z]{2}-[A-Z0-9]{3}"
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    else:
        return "-1"


def get_row_by_order_id(df, cc_id):
    print("", cc_id)
    is_adm_prefix = extract_prefix(cc_id)
    if is_adm_prefix != "-1":
        return "0"
    # Convert column values and search term to lowercase for case-insensitive comparison
    result_df = df[df["id_pedido"].astype(str) == cc_id]
    if not result_df.empty:
        # If there are multiple matches, you may need to decide how to handle them
        # desired_value = result_df.iloc[0]["id_pedido"]
        desired_value = result_df.iloc[0]["id_cliente"]
        return desired_value
    else:
        print("No matching rows found.")
        return "-1"


@bd_assets_route.route("/update_cc_client", methods=["PUT"])
def update_cc_assets():
    orders = get_order_results()
    # O que precisa ser feito aqui
    # Pegar aquela juncao os/ov e tranformar ela em um df
    df_orders = pd.DataFrame(orders)

    # Pegar o df de clientes
    model_to_dataframe(Client)
    df_CC = model_to_dataframe(CentroCustos)

    # Pegar o df de cc
    refs = []

    for index, row in df_CC.iterrows():
        print(index)
        CC = get_cc_id(row)
        DESC_CC = row["desc_centro_custos"]
        id_cc = row["id_centro_custos"]
        client_id = get_row_by_order_id(df_orders, CC)
        ref = {
            "CC": CC,
            "DESC_CC": DESC_CC,
            "id_cc": id_cc,
            "client_id": client_id,
        }
        if CC != "-1":
            client_by_cc(ref)
            refs.append(ref)

    return jsonify(
        {
            "orders": refs,
        }
    )
