# import os

import re

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request
from sqlalchemy.orm import class_mapper

from models import CentroCustos, db
from VHSYS.vhsys_cost_center import VHSYS_COST_CENTER


def extract_numeric_part(text):
    pattern = re.compile(r"\b(\d{6})\b")
    match = pattern.search(text)

    if match:
        return int(match.group(1))
    else:
        return -1


cost_center_route = Blueprint("CC", __name__)

load_dotenv()


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


def status_centro_custo(status):
    if status == "Ativo":
        return True
    return False


def status_lixeira(status):
    if status == "Sim":
        return True
    return False


# API route to add a new centro de custo
@cost_center_route.route("/cc/new", methods=["POST"])
def add_centro_custos():
    data = request.get_json()
    print("Data here", data)
    new_centro = CentroCustos(
        id_centro_custos=data["id_centro_custos"],
        desc_centro_custos=data["desc_centro_custos"],
        status_centro_custos=status_centro_custo(data["status_centro_custos"]),
        data_cad_centro=data["data_cad_centro"],
        lixeira=status_lixeira(data["lixeira"]),
        ref_centro_custos=extract_numeric_part(data["desc_centro_custos"]),
    )

    db.session.add(new_centro)
    db.session.commit()

    return jsonify({"message": "Centro de custo added successfully"}), 201


# API route to get all centro de custo
@cost_center_route.route("/cc", methods=["GET"])
def get_centro_custos():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    centros = CentroCustos.query.paginate(page, per_page, error_out=False)

    centro_list = []
    for centro in centros.items:
        centro_data = {
            "id_centro_custos": centro.id_centro_custos,
            "desc_centro_custos": centro.desc_centro_custos,
            "status_centro_custos": centro.status_centro_custos,
            "data_cad_centro": str(centro.data_cad_centro),
            "lixeira": centro.lixeira,
        }
        centro_list.append(centro_data)

    return jsonify(
        {
            "centros": centro_list,
            "total_pages": centros.pages,
            "current_page": centros.page,
            "total_items": centros.total,
        }
    )


@cost_center_route.route("/cc/ids", methods=["GET"])
def get_centro_custos_ids():
    all_ids = db.session.query(CentroCustos.id_centro_custos).all()
    all_ids = [row[0] for row in all_ids]

    return jsonify(
        {
            "ids": all_ids,
        }
    )


@cost_center_route.route("/cc/all", methods=["GET"])
def get_centro_custos_list():
    CC = get_objects_by_filters(CentroCustos, False)

    return jsonify(
        {
            "centros": CC,
        }
    )


@cost_center_route.route("/cc/update", methods=["PUT"])
def update_centro_custos():
    try:
        vhsys_cost_center = VHSYS_COST_CENTER()
        updates = vhsys_cost_center.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201


@cost_center_route.route("/cc/csv", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = CentroCustos.query.all()

    # Extract column names from the model
    column_names = [column.key for column in CentroCustos.__table__.columns]

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
            "Content-Disposition": "attachment; filename=cost_center.csv",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    return response
