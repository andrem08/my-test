import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify

from clockfy.clockfy_app_client import ClockifyAppClient
from models import Clock_Client

load_dotenv()

clock_client_route = Blueprint("CLOCK_CLIENT", __name__)


@clock_client_route.route("/clock/clock_client", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = Clock_Client.query.all()

    # Extract column names from the model
    column_names = [column.key for column in Clock_Client.__table__.columns]

    # Create a DataFrame from the orders
    all_registers_df = pd.DataFrame(
        [
            {col: getattr(register, col) for col in column_names}
            for register in all_registers
        ]
    )

    # Create a CSV string from the DataFrame
    csv_data = all_registers_df.to_csv(index=False)

    # Create a CSV response
    response = Response(
        csv_data,
        content_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=data.csv",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    return response


@clock_client_route.route("/clock/clock_client/update", methods=["PUT"])
def general_update():
    try:
        clock_client = ClockifyAppClient()
        updates = clock_client.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
