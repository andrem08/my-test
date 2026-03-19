from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from datetime import datetime
from report_manager import CC_REPORT_MANAGER
from update_extension_manager import get_actions_actual_status
from models import Update_extension_services, db

update_service_status = Blueprint("UPDATE_SERVICE_STATUS", __name__)

load_dotenv()


def get_register_data_by_id(id):
    return db.session.query(Update_extension_services).filter_by(ACTION=id).first()


def edit_existing_element(id, RUN_STATUS):
    existing_element = get_register_data_by_id(id)

    if existing_element is None:
        return None

    existing_element.RUN_STATUS = RUN_STATUS
    existing_element.LAST_UPDATE = datetime.utcnow()
    db.session.commit()
    print("Registro atualizado com sucesso")
    return existing_element


def update_all_records(RUN_STATUS):
    try:
        updated_rows = db.session.query(Update_extension_services).update(
            {Update_extension_services.RUN_STATUS: RUN_STATUS}, synchronize_session='fetch'
        )
        db.session.commit()
        return updated_rows
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@update_service_status.route("/clean_up", methods=["PUT"])
def cleanup_extension_service():
    try:
        update_all_records(0)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Update extension service status"}), 201


@update_service_status.route("/update_services", methods=["PUT"])
def update_extension_service():
    try:
        data = request.get_json()
        ACTION = data['ACTION']
        RUNNING_STATUS = data['RUNNING_STATUS']
        # print(f"\n \n Getting or data ref from  update_services {data}")
        edit_existing_element(ACTION, RUNNING_STATUS)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Update extension service status"}), 201


@update_service_status.route("/get_update_extension_service_data", methods=["GET"])
def get_update_extension_service_data():
    try:
        actions_get_actual_status = get_actions_actual_status()

        # Pegar o serviço e o atual estado e atualizar ele

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify(actions_get_actual_status), 201
