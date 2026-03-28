# import os

from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from models import Client, db
from VHSYS.vhsys_client import VHSYS_CLIENT

clients_route = Blueprint("CLIENT", __name__)

load_dotenv()


def verify_numeric_float(number):
    if number.isdigit():
        return float(number)
    return 0.0


def verify_numeric_int(number):
    if isinstance(number, int):
        return number
    if number.isdigit():
        return int(number)
    return 0.0


# API route to add a new centro de custo
@clients_route.route("/client/new", methods=["POST"])
def add_client():
    data = request.get_json()
    print("Data here", data, flush=True)
    new_client = Client(
        id_cliente=verify_numeric_int(data["id_cliente"]),
        id_cc=verify_numeric_int(data["id_cc"]),
        id_registro=verify_numeric_int(data["id_registro"]),
        tipo_cadastro=data["tipo_cadastro"],
        cnpj_cliente=data["cnpj_cliente"],
        razao_cliente=data["razao_cliente"],
        fantasia_cliente=data["fantasia_cliente"],
        endereco_cliente=data["endereco_cliente"],
        numero_cliente=data["numero_cliente"],
        bairro_cliente=data["bairro_cliente"],
        complemento_cliente=data["complemento_cliente"],
        referencia_cliente=data["referencia_cliente"],
        cep_cliente=data["cep_cliente"],
        cidade_cliente=data["cidade_cliente"],
        uf_cliente=data["uf_cliente"],
        tel_destinatario_cliente=data["tel_destinatario_cliente"],
        doc_destinatario_cliente=data["doc_destinatario_cliente"],
        nome_destinatario_cliente=data["nome_destinatario_cliente"],
        email_cliente=data["email_cliente"],
        data_cad_cliente=data["data_cad_cliente"],
        data_mod_cliente=data["data_mod_cliente"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_client)
    db.session.commit()

    return jsonify({"message": "Centro de custo added successfully"}), 201


# API route to get all centro de custo
@clients_route.route("/client", methods=["GET"])
def get_client():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    clients = Client.query.paginate(page, per_page, error_out=False)

    clients_list = []
    for client in clients.items:
        client_data = {
            "id_cliente": client.id_cliente,
            "id_registro": client.id_registro,
            "tipo_cadastro": client.tipo_cadastro,
            "cnpj_cliente": client.cnpj_cliente,
            "razao_cliente": client.razao_cliente,
            "fantasia_cliente": client.fantasia_cliente,
            "endereco_cliente": f"{client.endereco_cliente} {client.numero_cliente} {client.bairro_cliente} {client.cep_cliente} {client.cidade_cliente} {client.uf_cliente}",
            "tel_destinatario_cliente": client.tel_destinatario_cliente,
            "doc_destinatario_cliente": client.doc_destinatario_cliente,
            "nome_destinatario_cliente": client.nome_destinatario_cliente,
            "email_cliente": client.email_cliente,
            "data_cad_cliente": client.data_cad_cliente,
            "data_mod_cliente": client.data_mod_cliente,
        }
        clients_list.append(client_data)

    return jsonify(
        {
            "clients": clients_list,
            "total_pages": clients.pages,
            "current_page": clients.page,
            "total_items": clients.total,
        }
    )


@clients_route.route("/client/csv", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = Client.query.all()

    # Extract column names from the model
    column_names = [column.key for column in Client.__table__.columns]

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
            "Content-Disposition": "attachment; filename=orders.csv",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    return response


@clients_route.route("/client/update", methods=["PUT"])
def general_update():
    try:
        vhsys_client = VHSYS_CLIENT()
        updates = vhsys_client.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
