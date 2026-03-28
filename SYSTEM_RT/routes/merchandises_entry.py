import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from models import Extrato, db
from VHSYS.vhsys_merchandises_entry import VHSYS_MERCHANDISES_ENTRY

load_dotenv()

ACESS_TOKEN = os.getenv("vhsys_acess_token")
merch_route = Blueprint("merch", __name__)




@merch_route.route("/merch_entry", methods=["PUT"])
def general_update():
    try:
        vhsys_merch = VHSYS_MERCHANDISES_ENTRY()
        updates = vhsys_merch.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
