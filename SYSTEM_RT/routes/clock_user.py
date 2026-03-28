from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from clockfy.clockfy_user import ClockifyUser
from models import Clock_User, db

load_dotenv()

clock_user_route = Blueprint("CLOCK_USER", __name__)


def create_clock_user(data_dict):
    new_clock_user = Clock_User(
        id=data_dict.get("id"),
        email=data_dict.get("email"),
        name=data_dict.get("name"),
        profile_pic=data_dict.get("profile_pic"),
        active_workspace=data_dict.get("active_workspace"),
        default_workspace=data_dict.get("default_workspace"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(new_clock_user)
    db.session.commit()

    return new_clock_user


def edit_clock_user(clock_user, data_dict):
    if "id" in data_dict:
        clock_user.id = data_dict["id"]
    if "email" in data_dict:
        clock_user.email = data_dict["email"]
    if "name" in data_dict:
        clock_user.name = data_dict["name"]
    if "profile_pic" in data_dict:
        clock_user.profile_pic = data_dict["profile_pic"]
    if "active_workspace" in data_dict:
        clock_user.active_workspace = data_dict["active_workspace"]
    if "default_workspace" in data_dict:
        clock_user.default_workspace = data_dict["default_workspace"]

    clock_user.updated_at = datetime.utcnow()

    db.session.commit()

    return clock_user


@clock_user_route.route("/clock/clock_user", methods=["GET"])
def clock_user():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    extracts = Clock_User.query.paginate(page, per_page, error_out=False)

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


@clock_user_route.route("/clock/clock_user/edit", methods=["PUT"])
def clock_user_edit_route():
    try:
        data = request.get_json()
        edit_clock_user(Clock_User, data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Extract created successfully"}), 201


@clock_user_route.route("/clock/clock_user/new", methods=["POST"])
def clock_user_new_route():
    try:
        data = request.get_json()
        create_clock_user(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Extract created successfully"}), 201


@clock_user_route.route("/clock/clock_user/csv", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = Clock_User.query.all()

    # Extract column names from the model
    column_names = [column.key for column in Clock_User.__table__.columns]

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


@clock_user_route.route("/clock/clock_user/update", methods=["PUT"])
def general_update():
    try:
        clock_user = ClockifyUser()
        updates = clock_user.get_updates()
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
