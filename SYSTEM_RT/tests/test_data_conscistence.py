import json
import os
import unittest

import pandas as pd
from flask import Flask

from models import OrdersManage, Pedido, ServiceOrder, db

app = Flask(__name__)
DB_STRING = os.getenv("DB_STRING")
app.config["SQLALCHEMY_DATABASE_URI"] = DB_STRING
db.init_app(app)


class TestMergedData(unittest.TestCase):
    def model_to_dataframe(self, model):
        records = model.query.all()
        columns = [column.name for column in model.__table__.columns]
        data = [[getattr(record, column) for column in columns] for record in records]
        df = pd.DataFrame(data, columns=columns)
        return df

    def get_pedidos_origem_id(self):
        df = self.model_to_dataframe(Pedido)
        filtered_df = df[df["lixeira"] == "Nao"]
        column_series = filtered_df["id_ped"]
        column_array = column_series.values
        return column_array

    def get_service_order_origem_id(self):
        df = self.model_to_dataframe(ServiceOrder)
        filtered_df = df[df["lixeira"] == "Nao"]
        column_series = filtered_df["id_ordem"]
        column_array = column_series.values
        return column_array

    def get_order_manager_id(self):
        df = self.model_to_dataframe(OrdersManage)
        column_series = df["id_origem"]
        column_array = column_series.values
        return column_array

    def save_dict_to_json(self, dictionary, filename, indent=4):
        with open(filename, "w") as file:
            json.dump(dictionary, file, indent=indent)

    def test_orders_manage(self):
        with app.app_context():
            pedidos_id = self.get_pedidos_origem_id().tolist()  # Convert to list
            service_orders_ids = (
                self.get_service_order_origem_id().tolist()
            )  # Convert to list
            order_manager = self.get_order_manager_id().tolist()  # Convert to list

            ref = {
                "PEDIDOS_ID": pedidos_id,
                "PEDIDOS_SIZE": len(pedidos_id),
                "SERVICE_ORDER_ID": service_orders_ids,
                "SERVICE_ORDER_SIZE": len(service_orders_ids),
                "ORDER_MANAGER_IDS": order_manager,
                "ORDER_MANAGER_SIZE": len(order_manager),
            }
            self.save_dict_to_json(ref, "test_ref.json")


if __name__ == "__main__":
    unittest.main()
