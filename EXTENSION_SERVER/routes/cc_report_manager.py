from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

from report_manager import CC_REPORT_MANAGER

manage_cc_report_update = Blueprint("CC_REPORT_MANAGER", __name__)

load_dotenv()


# API route to add a new centro de custo
@manage_cc_report_update.route("/cc_report_manage/next_url", methods=["GET"])
def cc_report_manage_next_url():
    run_in_prod = True
    try:
        cc_report_manager = CC_REPORT_MANAGER()
        next_url = cc_report_manager.get_next_url()
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    if run_in_prod:
        return jsonify({"url": next_url}), 201
    return jsonify({"url": "not allowed to prod env"}), 201


@manage_cc_report_update.route("/cc_report_manage/status", methods=["GET"])
def update_cc_status_report():
    try:
        cc_report_manager = CC_REPORT_MANAGER()
        status = cc_report_manager.get_status_of_updating()
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify(status), 201
