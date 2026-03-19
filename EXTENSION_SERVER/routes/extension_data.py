import html

from flask import Blueprint, Flask, jsonify, request

from manage_cc_report_new import COST_REPORT_MANAGER, update_all_cc_status_to_zero

app = Flask(__name__)


cc_report_data = Blueprint("CC_REPORT_DATA", __name__)


def format_data_from_api(data):
    print("Data", data)


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


@cc_report_data.route("/cc_report", methods=["POST"])
def relatorio_new_entry_by_id():
    try:
        data = request.get_json()
        # print("\n \n \n Data from  CC_REPORT ", data)

        decoded_data = decode_html_entities(data)
        # print( "\n \n \n Decoded data HTML ENTITES", decoded_data)
        cc_manager = COST_REPORT_MANAGER(decoded_data)
        cc_manager.insert_page()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "GET A NEW CC_REPORT BY CC id"}), 201


@cc_report_data.route("/cc_report/reset", methods=["PUT"])
def reset_update():
    try:
        update_all_cc_status_to_zero()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "CC REPORT UPDATE RESETED"}), 201
