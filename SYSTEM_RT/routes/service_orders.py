import os
import re
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from models import ServiceOrder, db
from VHSYS.vhsys_service_order import VHSYS_SERVICE_ORDER

load_dotenv()

ACESS_TOKEN = os.getenv("vhsys_acess_token")
services_order_route = Blueprint("SO", __name__)


def verify_numeric_float(number):
    if number.isdigit():
        return float(number)
    return 0.0


def verify_numeric_int(number):
    if isinstance(number, int):
        return int(number)
    return 0.0


def extract_cc_value(input_string):
    # Define a regular expression pattern to find the value after "CC" or "CC "
    pattern = re.compile(r"CC[-\s]*(\d+)|CC[-\s]*")

    # Search for the pattern in the input string
    match = pattern.search(input_string)

    # If a match is found, return the matched value as an integer
    if match and match.group(1):
        return int(match.group(1))
    else:
        # If no match is found, return -1
        return -1


def create_order(data):
    new_service_order = ServiceOrder(
        nome_cliente=data["nome_cliente"],
        condicao_pagamento=data["condicao_pagamento"],
        condicao_pagamento_id=data["condicao_pagamento_id"],
        created_at=datetime.now(),
        data_cad_pedido=data["data_cad_pedido"],
        data_mod_pedido=data["data_mod_pedido"],
        ref_centro_custos=extract_cc_value(data["obs_interno_pedido"]),
        id_cliente=verify_numeric_int(data["id_cliente"]),
        id_ordem=verify_numeric_int(data["id_ordem"]),
        id_pedido=verify_numeric_int(data["id_pedido"]),
        lixeira=data["lixeira"],
        nota_servico_emitida=data["nota_servico_emitida"],
        obs_interno_pedido=data["obs_interno_pedido"],
        obs_pedido=data["obs_pedido"],
        referencia_ordem=data["referencia_ordem"],
        status_pedido=data["status_pedido"],
        tipo_servico=data["tipo_servico"],
        updated_at=datetime.now(),
        valor_total_desconto=float(data["valor_total_desconto"]),
        valor_total_despesas=float(data["valor_total_despesas"]),
        valor_total_pecas=float(data["valor_total_pecas"]),
        valor_total_os=float(data["valor_total_os"]),
        valor_total_servicos=float(data["valor_total_servicos"]),
    )
    db.session.add(new_service_order)
    db.session.commit()


@services_order_route.route("/os", methods=["GET"])
def orders_route():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    orders = ServiceOrder.query.paginate(page, per_page, error_out=False)

    orders_list = []
    for order in orders.items:
        order_data = {
            "id_ordem": order.id_ordem,
            "cliente": order.cliente,
            "cc": order.id_cc,
            "referencia": order.referencia_ordem,
            "valor_material": order.valor_material,
            "valor_total_despesas": order.valor_total_despesas,
            "obs_interna": order.obs_interno_pedido,
            "valor_total_servicos": str(order.valor_total_servicos),
        }
        orders_list.append(order_data)

    return jsonify(
        {
            "orders": orders_list,
            "total_pages": orders.pages,
            "current_page": orders.page,
            "total_items": orders.total,
        }
    )


@services_order_route.route("/os/new", methods=["POST"])
def orders_new_route():
    try:
        data = request.get_json()
        create_order(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Order created successfully"}), 201


@services_order_route.route("/os/update", methods=["PUT"])
def general_update():
    try:
        vhsys_os = VHSYS_SERVICE_ORDER()
        updates = vhsys_os.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201


@services_order_route.route("/os/csv", methods=["GET"])
def orders_csv_route():
    # Get all orders
    all_orders = ServiceOrder.query.all()

    # Extract column names from the model
    column_names = [column.key for column in ServiceOrder.__table__.columns]

    # Create a DataFrame from the orders
    orders_df = pd.DataFrame(
        [{col: getattr(order, col) for col in column_names} for order in all_orders]
    )

    # Create a CSV string from the DataFrame
    csv_data = orders_df.to_csv(index=False)

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
