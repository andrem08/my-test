import asyncio
from datetime import datetime

import pandas as pd

from models import Update_route_status, db
from utils.update_manage.telegram_manager import send_async_message

# Cria uma classe


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def get_update_status_by_route(route):
    query = db.session.query(Update_route_status).filter_by(route=route).first()
    return query


def update_route_update_status(route):
    # Get the existing ClockUser instance from the database
    print(f"Or route ref here : {route} ", flush=True)
    route_ref = get_update_status_by_route(route)

    # If the user doesn't exist, you might want to handle that case accordingly
    if route_ref is None:
        # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
        return None

    route_ref.runned = 1
    route_ref.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.session.commit()

    return route_ref


def update_route_status(route, start, end, logs_count, error_count):
    print(f"Or route ref here from update_status : {route} ", flush=True)
    route_ref = get_update_status_by_route(route)
    if route_ref is None:
        return None

    route_ref.start = start
    route_ref.end = end
    route_ref.logs_count = logs_count
    route_ref.error_count = error_count
    route_ref.updated_at = datetime.utcnow()
    db.session.commit()

    return route_ref


def update_all_route_update_status_to_zero():
    routes = db.session.query(Update_route_status).all()
    for route_ref in routes:
        route_ref.runned = 0
        route_ref.updated_at = (
            datetime.utcnow()
        ) 
    db.session.commit()

    return routes


class UPDATE_MANAGER:
    # Função de atualizar um campo de rota, após ele rodar

    # Função para pegar um numero de rotas e verificar quais rotas que ainda não foram rodadas, podem ser atualizadas

    # Função para verificar se todas as rotas foram atualizadas e zerar o status delas

    def __init__(self):
        print("Hello")

    def format_telegram_messages(self):
        routes_table = model_to_dataframe(Update_route_status)
        # Pega as n primeiras linhas
        output_message = "SYSTEM RT UPDATES"

        dict_array = routes_table.to_dict(orient="records")
        for elem in dict_array:
            start = elem["start"]
            end = elem["end"]
            logs_count = elem["logs_count"]
            error_count = elem["error_count"]
            time_difference = start - end
            message = f"""
                URL: {elem['route']}
                duration: {int(time_difference.seconds/1000)} sec
                err: {error_count}
                ins/edt: {logs_count}
                """
            output_message += message
        print(f"Output message {output_message}", flush=True)
        # send_async_message(output_message)
        # await send_async_message(output_message)
        asyncio.run(send_async_message(output_message))

    def get_not_runned_routes(self):
        routes_table = model_to_dataframe(Update_route_status)
        # Pega as n primeiras linhas
        dict_array = routes_table.to_dict(orient="records")
        updated = False

        # print(f"Routes table {dict_array}", flush=True)
        not_runned_elements = []
        for elem in dict_array:
            if elem["runned"] == 0:
                not_runned_elements.append(elem["route"])
        n_not_runned_urls = not_runned_elements[:3]
        if len(n_not_runned_urls) == 0:
            updated = True
            self.format_telegram_messages()
            # Rotina para setar tudo para zero de novo
        return {
            "updated": updated,
            "url_refs": n_not_runned_urls,
        }

    def update_runned_route(self, route):
        update_route_update_status(route)
        return route

    def update_route_status_atributes(self, route, start, end, logs_count, error_count):
        print(
            f"Os dados chegaram aqui {route}, {start}, {end}, {logs_count}, {error_count}",
            flush=True,
        )
        update_route_status(route, start, end, logs_count, error_count)
        return route

    def reset_runned_routes(self):
        update_all_route_update_status_to_zero()
        return "Updated"

    def get_actual_update_status(self):
        # update_all_route_update_status_to_zero()
        routes_table = model_to_dataframe(Update_route_status)
        # Pega as n primeiras linhas
        dict_array = routes_table.to_dict(orient="records")

        # print(f"Routes table {dict_array}", flush=True)
        not_runned_elements = []
        not_runned_urls = []
        runned_urls = []
        for elem in dict_array:
            if elem["runned"] == 0:
                not_runned_elements.append(elem["route"])
                not_runned_urls.append(elem["route"])
            else:
                runned_urls.append(elem["route"])
        # n_not_runned_urls = not_runned_elements[:3]
        return {
            "runned": len(runned_urls),
            "not_runned": len(not_runned_urls),
            "runned_urls": runned_urls,
            "not_runned_urls": not_runned_urls,
        }
