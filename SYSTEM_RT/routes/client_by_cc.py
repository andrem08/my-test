from datetime import datetime

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

from models import Client_by_CC, db

client_by_cc_route = Blueprint("CLIENT_BY_CC", __name__)

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


def create_client_by_cc(data):
    print(f"Calling for create client {data}", flush=True)
    new_relatorio = Client_by_CC(
        CC=data["CC"],
        PROJECT=data["PROJETO"],
        CLIENT=data["CLIENT"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.session.add(new_relatorio)
    db.session.commit()


# API route to add a new centro de custo
@client_by_cc_route.route("/client_by_cc/new", methods=["POST"])
def client_by_cc_new():
    try:
        data = request.get_json()
        create_client_by_cc(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Insert new CC report line successfully"}), 201
