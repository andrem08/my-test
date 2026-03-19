import html

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

from regular_bills_manage import REGULAR_BILLS_MANAGE

regular_bills = Blueprint("REGULAR_BILLS", __name__)

load_dotenv()


def generate_id_token(seed):
    import hashlib

    return hashlib.sha256(seed.encode()).hexdigest()


def decode_html_entities(data):
    if isinstance(data, dict):
        return {key: decode_html_entities(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [decode_html_entities(item) for item in data]
    elif isinstance(data, str):
        return html.unescape(data)
    else:
        return data


@regular_bills.route("/regular_bills", methods=["POST"])
def relatorio_new_entry_by_id():
    try:
        data = request.get_json()
        decoded_data = decode_html_entities(data)
        regular_bills = REGULAR_BILLS_MANAGE(decoded_data)
        regular_bills.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "GET A NEW regular_bills status "}), 201
