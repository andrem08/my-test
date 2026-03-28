from dotenv import load_dotenv
from flask import Blueprint, jsonify

from VHSYS.vhsys_categorias import VHSYS_CATEGORIAS

# from models import Client_by_CC, db

categoria_route = Blueprint("CATEGORIA", __name__)

load_dotenv()


@categoria_route.route("/category/update", methods=["PUT"])
def general_update():
    try:
        vhsys_client = VHSYS_CATEGORIAS()
        updates = vhsys_client.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
