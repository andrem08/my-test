from dotenv import load_dotenv
from flask import Blueprint, jsonify

from VHSYS.vhsys_contas_receber import VHSYS_CONTAS_RECEBER

load_dotenv()

account_inputs = Blueprint("ACCOUNT_INPUTS", __name__)


@account_inputs.route("/account_inputs/update", methods=["PUT"])
def general_update():
    try:
        account_inputs = VHSYS_CONTAS_RECEBER()
        updates = account_inputs.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
