import os
from dotenv import load_dotenv
from flask import Flask, request # Import the request object
from flask_cors import CORS
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from models import db
from routes.cc_report_manager import manage_cc_report_update
from routes.employers import employers
from routes.extension_data import cc_report_data
from routes.nf_report_manager import nf_report_manager
from routes.regular_bills import regular_bills
from routes.update_service_status import update_service_status
from routes.tangerino_entries import tangerino_entry_route

load_dotenv()

app = Flask(__name__)

@app.before_request
def log_all_requests():
    print("\n" * 2)
    print(f"➡️  Incoming Request: {request.method} {request.path}")
    DISPLAY_BODY = False
    if(DISPLAY_BODY):
        body = request.get_data(as_text=True)
        if body:
            print(f"📦 Body:\n{body}")
        else:
            print("📦 Body: [Empty]")
        print("\n" * 2)


app.config["TIMEOUT"] = 4096
app.config["SERVER_TIMEOUT"] = 4096


CORS(
    app,
    origins="*",
    methods=["GET", "POST", "PUT", "DELETE"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "test"],
)
app.config["CORS_HEADERS"] = "Content-Type"

# --- Blueprint Registration ---
app.register_blueprint(cc_report_data)
app.register_blueprint(manage_cc_report_update)
app.register_blueprint(regular_bills)
app.register_blueprint(employers)
app.register_blueprint(nf_report_manager)
app.register_blueprint(update_service_status)
app.register_blueprint(tangerino_entry_route)


DB_STRING = os.getenv("DB_STRING")
app.config["SQLALCHEMY_DATABASE_URI"] = DB_STRING
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


@app.route("/")
def hello_world():
    return "Extension report manager"


if __name__ == "__main__":
    app.run(debug=False)