from dotenv import load_dotenv
from flask import Blueprint, jsonify

from VHSYS.vhsys_nf import VHSYS_NF

load_dotenv()

nf_route = Blueprint("NF", __name__)


@nf_route.route("/nf/update", methods=["PUT"])
def general_update():
    try:
        nf = VHSYS_NF()
        updates = nf.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
