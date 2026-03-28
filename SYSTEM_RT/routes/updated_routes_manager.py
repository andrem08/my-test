from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

from utils.update_manage.route_update_status import ROUTE_UPDATE_STATUS
from utils.update_manage.update_manager import UPDATE_MANAGER

update_routes_manager_route = Blueprint("UPDATE_ROUTES_MANAGER", __name__)

load_dotenv()


# API route to add a new centro de custo
@update_routes_manager_route.route("/route_manager_info", methods=["GET"])
def route_manager_info():
    try:
        route_update_status = ROUTE_UPDATE_STATUS()
        route_update_status_as_json = route_update_status.get_all_as_json()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify(route_update_status_as_json), 201


# API route to add a new centro de custo
@update_routes_manager_route.route("/get_updated_routes", methods=["GET"])
def get_updated_routes():
    try:
        update_manager = UPDATE_MANAGER()
        not_runned_elements = update_manager.get_not_runned_routes()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify(not_runned_elements), 201


@update_routes_manager_route.route("/get_updated_routes_relation", methods=["GET"])
def update_routes_relation():
    try:
        update_manager = UPDATE_MANAGER()
        status = update_manager.get_actual_update_status()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify(status), 201


@update_routes_manager_route.route("/updated_routes_status", methods=["PUT"])
def update_route_status():
    try:
        data = request.get_json()
        route = data["route"]
        update_manager = UPDATE_MANAGER()
        not_runned_elements = update_manager.update_runned_route(route)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify(not_runned_elements), 201


@update_routes_manager_route.route("/updated_route_output", methods=["PUT"])
def update_route_output():
    try:
        data = request.get_json()
        route = data["route"]
        start = data["start"]
        end = data["end"]
        logs_count = data["logs_count"]
        error_count = data["error_count"]
        update_manager = UPDATE_MANAGER()
        not_runned_elements = update_manager.update_route_status_atributes(
            route, start, end, logs_count, error_count
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify(not_runned_elements), 201


@update_routes_manager_route.route("/reset_updated_routes_status", methods=["PUT"])
def reset_update_route_status():
    try:
        update_manager = UPDATE_MANAGER()
        update_manager.reset_runned_routes()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"reset": "done"}), 201
