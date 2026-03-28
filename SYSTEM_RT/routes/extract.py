import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from models import Extrato, db
from VHSYS.vhsys_extract import VHSYS_EXTRACT

load_dotenv()

ACESS_TOKEN = os.getenv("vhsys_acess_token")
extract_route = Blueprint("extract", __name__)


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


def create_extract(data):
    new_service_order = Extrato(
        id_fluxo=verify_numeric_int(data["id_fluxo"]),
        id_banco=verify_numeric_int(data["id_banco"]),
        nome_conta=data["nome_conta"],
        id_cliente=verify_numeric_int(data["id_cliente"]),
        nome_cliente=data["nome_cliente"],
        data_fluxo=data["data_fluxo"],
        valor_fluxo=verify_numeric_float(data["valor_fluxo"]),
        observacoes_fluxo=data["observacoes_fluxo"],
        id_centro_custos=data["id_centro_custos"],
        centro_custos_fluxo=data["centro_custos_fluxo"],
        id_categoria=verify_numeric_int(data["id_categoria"]),
        categoria_fluxo=data["categoria_fluxo"],
        forma_pagamento=data["forma_pagamento"],
        tipo_fluxo=data["tipo_fluxo"],
        data_cad_fluxo=data["data_cad_fluxo"],
        data_mod_fluxo=data["data_mod_fluxo"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        lixeira=data["lixeira"],
    )
    db.session.add(new_service_order)
    db.session.commit()


@extract_route.route("/extract", methods=["GET"])
def extracts_route():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    extracts = Extrato.query.paginate(page, per_page, error_out=False)

    extracts_list = []
    for extract in extracts.items:
        extract_data = {
            "id_fluxo": extract.id_fluxo,
            "id_banco": extract.id_banco,
            "nome_conta": extract.nome_conta,
            # Add other fields as needed
            "updated_at": extract.updated_at,
        }
        extracts_list.append(extract_data)

    return jsonify(
        {
            "extracts": extracts_list,
            "total_pages": extracts.pages,
            "current_page": extracts.page,
            "total_items": extracts.total,
        }
    )


@extract_route.route("/extract/new", methods=["POST"])
def extract_new_route():
    try:
        data = request.get_json()
        create_extract(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Extract created successfully"}), 201


@extract_route.route("/extract/csv", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = Extrato.query.all()

    # Extract column names from the model
    column_names = [column.key for column in Extrato.__table__.columns]

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


@extract_route.route("/extract/update", methods=["PUT"])
def general_update():
    try:
        vhsys_extract = VHSYS_EXTRACT()
        updates = vhsys_extract.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
