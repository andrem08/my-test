import re
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, Response, jsonify, request

from clockfy.clockfy_hour_entry_new import ClockifyHourEntry
from models import Clock_Time_Entry, PrimaData, db

load_dotenv()

clock_hour_entry_route = Blueprint("CLOCK_ENTRY", __name__)


def combine_date_time(date_str, time_str):
    # Convert date string to datetime object
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")

    # Convert time string to datetime object
    time_obj = datetime.strptime(time_str, "%H:%M")

    # Combine date and time
    combined_datetime = datetime(
        date_obj.year, date_obj.month, date_obj.day, time_obj.hour, time_obj.minute
    )

    return combined_datetime


def join_tags(self, tags):
    if tags is None:
        return "no-tags"
    return ",".join(tags)


def convert_time_to_minutes(time_string):
    match = re.match(r"PT(\d+)H(?:(\d+)M)?(?:(\d+)S)?", time_string)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        total_minutes = hours * 60 + minutes + seconds / 60
        return total_minutes
    else:
        return -1


def create_clock_hour_entry(time_entry):
    # Verificando se o id existe, caso contrario criar um campo de id invalido na tabela com um novo id

    ref = {
        "id": time_entry.get("id"),
        "description": time_entry.get("description"),
        "tags_id": join_tags(time_entry.get("tagIds")),
        "project_id": -1,
        "interval_start_moment": time_entry["timeInterval"].get("start"),
        "interval_end_moment": time_entry["timeInterval"].get("end"),
        "interval_duration": time_entry["timeInterval"].get("duration"),
        "interval_duration_minutes": convert_time_to_minutes(
            time_entry["timeInterval"].get("duration")
        ),
        "user_id": time_entry.get("userId"),
        "source": "api",
    }
    try:
        new_clock_time_entry = Clock_Time_Entry(
            id=ref.get("id"),
            description=ref.get("description"),
            user_id=ref.get("user_id"),
            project_id=ref.get("project_id"),
            tags_id=ref.get("tags_id"),
            interval_start_moment=ref.get("interval_start_moment"),
            interval_end_moment=ref.get("interval_end_moment"),
            interval_duration=ref.get("interval_duration"),
            interval_duration_minutes=ref.get("interval_duration_minutes"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(new_clock_time_entry)
        db.session.commit()
        print("Inserindo o registro ", ref, flush=True)
        return new_clock_time_entry
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def create_prima_entry(ref):
    new_service_order = PrimaData(
        ID=ref.get("ID"),
        CENTRO_DE_CUSTO=ref.get("CENTRO_DE_CUSTO"),
        PROJETO=ref.get("PROJETO"),
        CLIENTE=ref.get("CLIENTE"),
        DESCRICAO=ref.get("DESCRICAO"),
        TAREFA=ref.get("TAREFA"),
        USUARIO=ref.get("USUARIO"),
        ATIVIDADE=ref.get("ATIVIDADE"),
        DATA_INICIO=ref.get("DATA_INICIO"),
        HORA_INICIO=ref.get("HORA_INICIO"),
        DATA_FINAL=ref.get("DATA_FINAL"),
        HORA_FINAL=ref.get("HORA_FINAL"),
        interval_start_moment=combine_date_time(
            ref.get("DATA_INICIO"), ref.get("HORA_INICIO")
        ),
        interval_end_moment=combine_date_time(
            ref.get("DATA_FINAL"), ref.get("HORA_FINAL")
        ),
        time_difference_in_minutes=ref.get("time_difference_in_minutes"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(new_service_order)
    db.session.commit()


@clock_hour_entry_route.route("/clock/clock_entry", methods=["GET"])
def to_csv_route():
    # Get all orders
    all_registers = Clock_Time_Entry.query.all()

    # Extract column names from the model
    column_names = [column.key for column in Clock_Time_Entry.__table__.columns]

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


@clock_hour_entry_route.route("/clock/prima_entry", methods=["GET"])
def to_prima_csv_route():
    # Get all orders
    all_registers = PrimaData.query.all()

    # Extract column names from the model
    column_names = [column.key for column in PrimaData.__table__.columns]

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
            "Content-Disposition": "attachment; filename=prima-data.csv",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    return response


@clock_hour_entry_route.route("/clock/prima", methods=["POST"])
def prima_clock_appointement():
    try:
        data = request.get_json()
        print(f" \n \n Prima data {data} ", flush=True)
        create_prima_entry(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "prima register created successfully"}), 201


@clock_hour_entry_route.route("/clock/hour_entry", methods=["POST"])
def clock_appointement():
    try:
        data = request.get_json()
        response = create_clock_hour_entry(data)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({response}), 201


@clock_hour_entry_route.route("/clock/clock_entry/update", methods=["PUT"])
def general_update():
    try:
        clock_hour_entry = ClockifyHourEntry()
        updates = clock_hour_entry.get_updates()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    return jsonify(updates), 201


@clock_hour_entry_route.route("/clock/clock_api", methods=["GET"])
def orders_csv_route():
    # Get all orders

    clock_hour_entry = ClockifyHourEntry()
    api_result = clock_hour_entry.get_api()
    api_df = pd.DataFrame(api_result)
    # json_data = jsonify()
    print(f"Api  formated result here {api_result}", flush=True)
    # json_data = jsonify(api_result)
    # Create a CSV string from the DataFrame
    csv_data = api_df.to_csv(index=False)

    # Create a CSV response
    response = Response(
        response=csv_data,
        content_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=clock_api.csv",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    return response
