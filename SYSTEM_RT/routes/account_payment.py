from dotenv import load_dotenv
from flask import Blueprint, jsonify

from VHSYS.vhsys_contas import VHSYS_CONTAS

load_dotenv()

account_payment = Blueprint("ACCOUNT_PAYMENT", __name__)


@account_payment.route("/account_payment/update", methods=["PUT"])
def general_update():
    try:
        account_pay = VHSYS_CONTAS()
        updates = account_pay.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
