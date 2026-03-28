import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify

from clockfy.clockfy_project import ClockifyProject
from models import Clock_Project

load_dotenv()

clock_project_route = Blueprint("CLOCK_PROJECT", __name__)


@clock_project_route.route("/clock/clock_project", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = Clock_Project.query.all()

    # Extract column names from the model
    column_names = [column.key for column in Clock_Project.__table__.columns]

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


@clock_project_route.route("/clock/clock_project/update", methods=["PUT"])
def general_update():
    try:
        clock_project = ClockifyProject()
        updates = clock_project.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201
