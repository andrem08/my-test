from dotenv import load_dotenv
from tangerino.tangerino_time_entry import TangerinoTimeEntry
from flask import Blueprint, jsonify
load_dotenv()

tangerino_entry_route = Blueprint("TANGERINO_ENTRY", __name__)

@tangerino_entry_route.route("/tagerino/time_entry", methods=["PUT"])
def update_tangerino_entries():
    try:
        tangerino_time_entry = TangerinoTimeEntry()
        tangerino_time_entry.update_report()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Tangerino data updated successfully"}), 201
