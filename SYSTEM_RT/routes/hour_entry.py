import datetime

from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from clockfy.clockfy_app_client import ClockifyAppClient
from models import Contexted_hour_entry, db

load_dotenv()

hour_entry_route = Blueprint("HOUR_ENTRY", __name__)


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


def create_hour_entry(data):
    new_service_order = Contexted_hour_entry(
        CC=verify_numeric_int(data["CC"]),
        PROJETO=data["PROJETO"],
        CLIENTE=data["CLIENTE"],
        DESCRICAO=data["DESCRICAO"],
        USUARIO=data["USUARIO"],
        GRUPO=data["GRUPO"],
        ATIVIDADE=data["ATIVIDADE"],
        DATA_INICIO=data["DATA_INICIO"],  # Assuming date is stored as string
        HORA_INICIO=data["HORA_INICIO"],  # Assuming time is stored as string
        DATA_FINAL=data["DATA_FINAL"],
        HORA_FINAL=data["HORA_FINAL"],
        HORAS_MINUTOS=data["HORAS_MINUTOS"],
        HH_VENDA=data["HH_VENDA"],
        HH_INTERNO=data["HH_INTERNO"],
        ORIGEM=data["ORIGEM"],
        SEED=data["SEED"],
        TOKEN=data["TOKEN"],
        interval_start_moment=data["interval_start_moment"],
        interval_end_moment=data["interval_end_moment"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.session.add(new_service_order)
    db.session.commit()


@hour_entry_route.route("/hour_entry/new", methods=["POST"])
def extract_new_route():
    try:
        data = request.get_json()
        create_hour_entry(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Extract created successfully"}), 201


@hour_entry_route.route("/clock/clock_client/update", methods=["PUT"])
def general_update():
    try:
        clock_client = ClockifyAppClient()
        updates = clock_client.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201


@hour_entry_route.route("/clock/clock_api", methods=["GET"])
def orders_csv_route():
    # Get all orders

    clock_client = ClockifyAppClient()
    api_df = clock_client.get_updates()

    # Create a CSV string from the DataFrame
    csv_data = api_df.to_csv(index=False)

    # Create a CSV response
    response = Response(
        csv_data,
        content_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=clock_api.csv",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    return response
