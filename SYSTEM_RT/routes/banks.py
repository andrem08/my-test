from dotenv import load_dotenv
from flask import Blueprint, jsonify

from VHSYS.vhsys_banks import VHSYS_BANKS

load_dotenv()

banks_route = Blueprint("BANKS", __name__)


@banks_route.route("/banks/update", methods=["PUT"])
def general_update():
    try:
        banks = VHSYS_BANKS()
        updates = banks.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
