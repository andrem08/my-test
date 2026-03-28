import os

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify

from models import Client, Client_by_CC, Clock_User
from utils.orders_manager import OrdersManager
from utils.queries.cost_center_report_query import COST_CENTER_REPORT
from utils.update_cc_by_client import CLIENT_BY_CC_MANAGER

load_dotenv()

ACESS_TOKEN = os.getenv("vhsys_acess_token")
views_route = Blueprint("VIEW", __name__)


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def dataframe_to_list_of_dicts(df, columns=None):
    if columns is None:
        columns = df.columns.tolist()

    result_list = [dict(zip(columns, values)) for values in df[columns].values]

    return result_list


@views_route.route("/view/orders", methods=["GET"])
def view_order_route():
    try:
        om = OrdersManager()
        result = om.get_order_results()
        return jsonify(
            {
                "result": result,
            }
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}", flush=True)
        return jsonify({"error": "Internal Server Error"}), 500


@views_route.route("/orders/update", methods=["PUT"])
def general_update():
    try:
        order_manager = OrdersManager()
        updates = order_manager.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201


@views_route.route("/cc_by_client/update", methods=["PUT"])
def cc_by_client_update():
    try:
        client_by_cc = CLIENT_BY_CC_MANAGER()
        updates = client_by_cc.update_cc_by_id()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201


@views_route.route("/view/cc_report_total", methods=["GET"])
def total_by_cc_report():
    cc_report = COST_CENTER_REPORT()
    try:
        cc_report.get_report()
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify([]), 201


@views_route.route("/view/client_by_cc_info", methods=["GET"])
def client_by_cc_report():
    # cc_report = COST_CENTER_REPORT()

    try:
        cc_df = model_to_dataframe(Client_by_CC)
        selected_columns = ["CC", "id_cc", "ref_cc"]
        result_dict = dataframe_to_list_of_dicts(cc_df, columns=selected_columns)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(result_dict), 201


@views_route.route("/view/orders/csv", methods=["GET"])
def orders_csv_route():
    om = OrdersManager()
    result = om.get_order_results()
    df = pd.DataFrame(result)
    # Create a CSV string from the DataFrame
    csv_data = df.to_csv(index=False)

    # Create a CSV response
    response = Response(
        csv_data,
        content_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=orders.csv",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    return response


def get_user_info():
    user = model_to_dataframe(Clock_User)
    client = model_to_dataframe(Client)
    user_ref = []
    for index, row in user.iterrows():
        row_dict = row.to_dict()
        mail = row_dict["email"]
        user_name = row_dict["name"]
        profile_pic = row_dict["profile_pic"]
        cli_row = client[client["email_cliente"] == mail]

        if not cli_row.empty:  # Check if cli_row is not empty
            cli_row_dict = cli_row.head(1).to_dict(orient="records")[
                0
            ]  # Access the first dictionary in the list
            email = cli_row_dict["email_cliente"]
            nome_cliente = cli_row_dict["razao_cliente"]
            # print(f" row ref  {email}")
            ref = {
                "email": email,
                "profile_picture": profile_pic,
                "user_name": user_name,
                "nome": nome_cliente,
            }
            user_ref.append(ref)
            print("ref", ref)
        else:
            print(f"No client found for email: {mail}")
    return user_ref


@views_route.route("/view/userInfo", methods=["GET"])
def clock_users_route():
    # Create a CSV string from the DataFrame
    try:
        user_info = get_user_info()
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(user_info), 201
