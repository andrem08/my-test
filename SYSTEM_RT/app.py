import os

import sentry_sdk
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint

from models import db
from routes.account_inputs import account_inputs
from routes.account_payment import account_payment
from routes.auxiliar_data import auxiliar_data
from routes.banks import banks_route
from routes.bd_assets import bd_assets_route
from routes.buy_order import buy_order_route
from routes.categoria import categoria_route
from routes.cc_report_manager import manage_cc_report_update
from routes.client import clients_route
from routes.client_by_cc import client_by_cc_route
from routes.clock_client import clock_client_route
from routes.clock_hour_entry import clock_hour_entry_route
from routes.clock_project import clock_project_route
from routes.clock_tags import clock_tags_route
from routes.clock_user import clock_user_route
from routes.contexted_hours import contexted_hours_route
from routes.cost_center import cost_center_route
from routes.extract import extract_route
from routes.merchandises_entry import merch_route
from routes.nf import nf_route
from routes.pedido import pedido_route
from routes.products import products_route
from routes.relatorio_cc import relatorio_cc_route
from routes.service_orders import services_order_route
from routes.table_statistic import tables_statistcs_route
from routes.tangerino_entries import tangerino_entry_route
from routes.updated_routes_manager import update_routes_manager_route
from routes.views import views_route

# from sentry_sdk.integrations.flask import FlaskIntegration



load_dotenv()

SWAGGER_URL = "/swagger"
API_URL = "/static/swagger.json"

app = Flask(__name__)

# # Sentry Configuration
# sentry_sdk.init(
#     dsn="https://3c367a1a7d1ff8ae3b27ae64ce6a7171@o4506383500443648.ingest.us.sentry.io/4509904716693504",
#     integrations=[
#         FlaskIntegration(),
#     ],
#     # Set traces_sample_rate to 1.0 to capture 100%
#     # of transactions for performance monitoring.
#     traces_sample_rate=1.0,
#     send_default_pii=True,
# )


swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "RT Stock Manager"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

app.register_blueprint(services_order_route)
app.register_blueprint(cost_center_route)
app.register_blueprint(clients_route)
app.register_blueprint(extract_route)
app.register_blueprint(pedido_route)
app.register_blueprint(views_route)
app.register_blueprint(clock_user_route)
app.register_blueprint(clock_client_route)
app.register_blueprint(clock_project_route)
app.register_blueprint(clock_hour_entry_route)
app.register_blueprint(relatorio_cc_route)
app.register_blueprint(clock_tags_route)
app.register_blueprint(account_payment)
app.register_blueprint(client_by_cc_route)
app.register_blueprint(tables_statistcs_route)
app.register_blueprint(buy_order_route)
app.register_blueprint(bd_assets_route)
app.register_blueprint(contexted_hours_route)
app.register_blueprint(banks_route)
app.register_blueprint(account_inputs)
app.register_blueprint(update_routes_manager_route)
app.register_blueprint(categoria_route)
app.register_blueprint(manage_cc_report_update)
app.register_blueprint(tangerino_entry_route)
app.register_blueprint(nf_route)
app.register_blueprint(merch_route)
app.register_blueprint(products_route)
app.register_blueprint(auxiliar_data)


CONTEXT = os.getenv("CONTEXT")
DB_STRING = os.getenv("DB_STRING")


app.config["SQLALCHEMY_DATABASE_URI"] = DB_STRING
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TIMEOUT"] = 4096
db.init_app(app)
migrate = Migrate(app, db, render_as_batch=True)
CORS(
    app,
    origins="*",
    methods=["GET", "POST", "PUT", "DELETE"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "test"],
)
app.config["CORS_HEADERS"] = "Content-Type"


@app.before_request
def authenticate_request():
    query_parameters = request.args
    print("query_parameters", query_parameters, flush=True)
    print("token", query_parameters.get("rt_token"), flush=True)
    RT_TOKEN = os.getenv("RT_TOKEN")
    if query_parameters.get("rt_token") != RT_TOKEN:
        return jsonify({"error": "unathorized"}), 401


@app.route("/")
def hello_world():
    print("Ola ", flush=True)
    print("Running")
    # You can add a test error here if you want, like 1/0
    return f"Hello from {CONTEXT}!"


# @app.route("/route-graph")
# def route_graph():
#     graph = {"nodes": [], "links": []}
#     blueprint_nodes = set()

#     # Add the central 'app' node
#     graph["nodes"].append(
#         {
#             "id": "app",
#             "label": "App",
#             "group": 0,  # Central node
#             "color": "#ffcccc",  # Light red
#         }
#     )

#     for rule in app.url_map.iter_rules():
#         blueprint_name = rule.endpoint.split(".")[
#             0
#         ]  # Get the blueprint name from the endpoint

#         if blueprint_name != "app":  # Skip the central node for blueprints
#             if blueprint_name not in blueprint_nodes:
#                 blueprint_nodes.add(blueprint_name)
#                 graph["nodes"].append(
#                     {
#                         "id": blueprint_name,
#                         "label": f"Blueprint: {blueprint_name}",
#                         "group": 1,
#                         "color": "#ccffcc",
#                     }
#                 )

#                 graph["links"].append({"source": "app", "target": blueprint_name})

#         methods = ", ".join(rule.methods - {"HEAD", "OPTIONS"})
#         route_name = f"{rule.rule} ({methods})"

#         graph["nodes"].append(
#             {
#                 "id": route_name,
#                 "label": route_name,
#                 "group": 2,  # Route nodes
#                 "color": "#ccccff",  # Light blue
#             }
#         )

#         # Connect routes to their respective blueprint nodes
#         graph["links"].append({"source": blueprint_name, "target": route_name})

#     return jsonify(graph)


def main():
    # Usage example:

    app.app_context()
    # Run with debug=False for Sentry to capture events
    app.run(debug=False)


# Run the Flask application
if __name__ == "__main__":
    main()
