from datetime import datetime

import pandas as pd

from models import CentroCustos, Update_cc_report_status, db


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def create_new_update_status(cc_id):
    print(f"Calling for create new update status for id {cc_id}", flush=True)
    new_relatorio = Update_cc_report_status(
        cc_id=cc_id,
        entries_runned=0,
        outputs_runned=0,
        updated_at=datetime.now(),
    )

    db.session.add(new_relatorio)
    db.session.commit()


def get_current_date():
    # Get current date
    current_date = datetime.now()

    # Format the date as dd/mm/yyyy
    formatted_date = current_date.strftime("%d/%m/%Y")

    return formatted_date


# def update_output(id):
#     # Get the existing ClockUser instance from the database
#     existing_user = db.session.query(Update_cc_report_status).filter_by(id=id).first()

#     # If the user doesn't exist, you might want to handle that case accordingly
#     if existing_user is None:
#         # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
#         return None

#     if "name" in data_dict:
#         existing_user.name = data_dict["name"]
#     if "note" in data_dict:
#         existing_user.note = data_dict["note"]

#     # Update the 'updated_at' property
#     existing_user.updated_at = datetime.utcnow()

#     # Commit the changes to the database
#     db.session.commit()

#     return existing_user


def verify_cc_changes():
    cc_df = model_to_dataframe(CentroCustos)
    cc_ids = cc_df["id_centro_custos"].values
    print(f"CC_DF {cc_ids}", flush=True)
    cc_report_status_df = model_to_dataframe(Update_cc_report_status)
    cc_report_status = cc_report_status_df["cc_id"].values
    print(f"CC_REPORT_STATUS {cc_report_status}", flush=True)

    for ref_cc in cc_ids:
        print(f"ref cc {ref_cc}", flush=True)
        if ref_cc in cc_report_status:
            print("Já existe")
        else:
            print(f"Registro que precisa ser inserido {ref_cc}", flush=True)
            create_new_update_status(ref_cc)


class CC_REPORT_MANAGER:
    def __init__(self):
        verify_cc_changes()
        print("Hello")

    def update_cc_id_status(self, cc_id, type_ref):
        cc_manager = (
            db.session.query(Update_cc_report_status).filter_by(cc_id=cc_id).first()
        )

        # If the user doesn't exist, you might want to handle that case accordingly
        if cc_manager is None:
            # Handle non-existent user (e.g., raise an exception, return an error response, etc.)
            return None

        if type_ref == "E":
            if "entries_runned" in cc_manager:
                cc_manager.entries_runned = 1
        if type_ref == "S":
            if "outputs_runned" in cc_manager:
                cc_manager.outputs_runned = 1

        # Update the 'updated_at' property
        cc_manager.updated_at = datetime.utcnow()

        # Commit the changes to the database
        db.session.commit()

        return cc_manager

    def get_url(self, id, type):
        print(f"ID {id}", flush=True)
        actual_day_date = get_current_date()
        url = f"https://app.vhsys.com.br/Relatorio/Relatorio.CentroCustos.JSON.php?considerarData=pagamento&Data1=01/01/2002&Data2={actual_day_date}&ListarCentroAtivoSemLancamento=1&modelo=2&Nome=&Cod=&Tipo={type}&Centro={id}&Categoria=null&buscar=1"
        return url

    def get_next_url(self):
        cc_report_status_df = model_to_dataframe(Update_cc_report_status)
        for index, row in cc_report_status_df.iterrows():
            # print(f"df_row {index} , {row} ", flush=True)
            CC_ID = row["cc_id"]
            ENTRY = row["entries_runned"]
            OUTPUT = row["outputs_runned"]
            print(f"cc_id {row['cc_id']}")
            print(f"Entry here {ENTRY}", flush=True)
            print(f"Output here {OUTPUT}", flush=True)
            print("Index", index)
            if ENTRY == 0:
                print("Entry")
                return {
                    "cc_id": CC_ID,
                    "url": self.get_url(CC_ID, "Entrada"),
                    "type": "entry",
                }
            if OUTPUT == 0:
                return {
                    "cc_id": CC_ID,
                    "url": self.get_url(CC_ID, "Saida"),
                    "type": "output",
                }
                print("output")

    def get_status_of_updating(self):
        cc_report_status_df = model_to_dataframe(Update_cc_report_status)
        total_lines = len(cc_report_status_df)
        number_of_entries = len(
            cc_report_status_df[cc_report_status_df["entries_runned"] == 1]
        )
        number_of_outputs = len(
            cc_report_status_df[cc_report_status_df["outputs_runned"] == 1]
        )

        running = True

        if number_of_entries == number_of_outputs and number_of_entries == total_lines:
            running = False
        return {
            "running": running,
            "total_lines": total_lines,
            "number_of_entries": number_of_entries,
            "number_of_outputs": number_of_outputs,
        }
