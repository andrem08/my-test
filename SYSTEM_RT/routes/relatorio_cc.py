from datetime import datetime

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

relatorio_cc_route = Blueprint("RELATORIO_CC", __name__)

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


def generate_id_token(seed):
    import hashlib

    return hashlib.sha256(seed.encode()).hexdigest()


def extract_date_from_string(string):
    string = string.replace("Pago", "").strip()
    string = string.replace("(", "").strip()
    string = string.replace(")", "").strip()
    date = string.split()[0]
    date_obj = datetime.strptime(date, "%d/%m/%Y")
    date_str = date_obj.isoformat()
    return date_str


@relatorio_cc_route.route("/cc_report/new_entry_by_id", methods=["POST"])
def relatorio_new_entry_by_id():
    print("Aqui esta", flush=True)
    try:
        data = request.get_json()
        print(f"Data , {data}", flush=True)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Insert new CC report line successfully"}), 201
