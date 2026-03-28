from dotenv import load_dotenv
from flask import Blueprint, jsonify

from auxiliar_data.hh_value import EXTERNAL_DATA_HH_VALUE

load_dotenv()

auxiliar_data = Blueprint("AUXILIAR_DATA", __name__)


@auxiliar_data.route("/auxiliar_data/employer_hh/update", methods=["PUT"])
def general_update():
    try:
        external_data_hh = EXTERNAL_DATA_HH_VALUE()
        updates = external_data_hh.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
