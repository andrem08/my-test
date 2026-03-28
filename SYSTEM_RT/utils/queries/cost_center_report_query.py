import pandas as pd

from models import Relatorio_CC


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def group_elements_by_key(input_array, key):
    grouped_elements = {}

    for element in input_array:
        element_key = element.get(key)

        if element_key is not None:
            if element_key not in grouped_elements:
                grouped_elements[element_key] = []

            grouped_elements[element_key].append(element)

    return list(grouped_elements.values())


class COST_CENTER_REPORT:
    def __init__(self):
        self.all_ids = []

    def get_report(self):
        relatorio_cc_df = model_to_dataframe(Relatorio_CC)
        relatorio_cc_ref = relatorio_cc_df.to_dict(orient="records")
        grouped = group_elements_by_key(relatorio_cc_ref, "ID_CC")
        for group in grouped:
            sum_values = 0
            id_cc = group[0].get("ID_CC")
            # print(f" {id_cc}", flush=True)
            for reg in group:
                if reg.get("TYPE") == "saida":
                    # print(f" {reg} ", flush=True)
                    sum_values += reg.get("VALOR")
            ref = {"ID_CC": id_cc, "total_value": sum_values}
            print(ref, flush=True)
