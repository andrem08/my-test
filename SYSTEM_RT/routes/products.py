import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from models import Extrato, db
from VHSYS.vhsys_product import VHSYS_PRODUCT
from VHSYS.vhsys_products_entry import VHSYS_PRODUCT_ENTRY

load_dotenv()

ACESS_TOKEN = os.getenv("vhsys_acess_token")
products_route = Blueprint("products", __name__)


@products_route.route("/merch_products", methods=["PUT"])
def merch_products_update():
    try:
        vhsys_merch = VHSYS_PRODUCT_ENTRY()
        updates = vhsys_merch.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201


@products_route.route("/products", methods=["PUT"])
def products_update():
    try:
        vhsys_merch = VHSYS_PRODUCT()
        updates = vhsys_merch.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
