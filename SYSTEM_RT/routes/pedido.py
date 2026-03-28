from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from models import Pedido, db
from VHSYS.vhsys_requests import VHSYS_REQUESTS

pedido_route = Blueprint("PEDIDO", __name__)

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
@pedido_route.route("/pedido/new", methods=["POST"])
def add_pedido():
    data = request.get_json()
    print("Data here", data, flush=True)
    new_pedido = Pedido(
        id_ped=verify_numeric_int(data["id_ped"]),
        id_pedido=verify_numeric_int(data["id_pedido"]),
        id_cliente=verify_numeric_int(data["id_cliente"]),
        nome_cliente=data["nome_cliente"],
        cc=data["cc"],
        vendedor_pedido=data["vendedor_pedido"],
        valor_total_produtos=data["valor_total_produtos"],
        desconto_pedido=data["desconto_pedido"],
        desconto_pedido_porc=data["desconto_pedido_porc"],
        peso_total_nota=data["peso_total_nota"],
        peso_total_nota_liq=data["peso_total_nota_liq"],
        frete_pedido=data["frete_pedido"],
        valor_total_nota=data["valor_total_nota"],
        valor_baseICMS=data["valor_baseICMS"],
        valor_ICMS=data["valor_ICMS"],
        valor_baseST=data["valor_baseST"],
        valor_ST=data["valor_ST"],
        valor_IPI=data["valor_IPI"],
        condicao_pagamento_id=data["condicao_pagamento_id"],
        condicao_pagamento=data["condicao_pagamento"],
        frete_por_pedido=data["frete_por_pedido"],
        data_pedido=data["data_pedido"],
        prazo_entrega=data["prazo_entrega"],
        referencia_pedido=data["referencia_pedido"],
        obs_pedido=data["obs_pedido"],
        obs_interno_pedido=data["obs_interno_pedido"],
        status_pedido=data["status_pedido"],
        data_cad_pedido=data["data_cad_pedido"],
        data_mod_pedido=data["data_mod_pedido"],
        lixeira=data["lixeira"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_pedido)
    db.session.commit()

    return jsonify({"message": "Centro de custo added successfully"}), 201


@pedido_route.route("/pedido/csv", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = Pedido.query.all()

    # Extract column names from the model
    column_names = [column.key for column in Pedido.__table__.columns]

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


@pedido_route.route("/ov/update", methods=["PUT"])
def general_update():
    try:
        vhsys_ov = VHSYS_REQUESTS()
        updates = vhsys_ov.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
