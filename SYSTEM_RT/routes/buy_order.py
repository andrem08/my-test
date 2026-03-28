import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify

from models import Buy_order
from VHSYS.vhsys_buy_order import VHSYS_BUY_ORDER

load_dotenv()

buy_order_route = Blueprint("BUY_ORDER", __name__)


@buy_order_route.route("/buy_order/", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = Buy_order.query.all()

    # Extract column names from the model
    column_names = [column.key for column in Buy_order.__table__.columns]

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


@buy_order_route.route("/buy_order/update", methods=["PUT"])
def general_update():
    try:
        vhsys_buy_order = VHSYS_BUY_ORDER()
        updates = vhsys_buy_order.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
