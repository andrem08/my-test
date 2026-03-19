from datetime import datetime

import pandas as pd

from models import CentroCustos, Update_cc_report_status, db
from update_extension_manager import UPDATE_EXTENSION_STATUS


def model_to_dataframe(model):
    records = model.query.all()
    columns = [column.name for column in model.__table__.columns]
    data = [[getattr(record, column) for column in columns] for record in records]
    df = pd.DataFrame(data, columns=columns)
    return df


def create_new_update_status(cc_id):
    # print(f"Calling for create client {cc_id}", flush=True)
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


def verify_cc_changes():
    cc_df = model_to_dataframe(CentroCustos)
    cc_ids = cc_df["id_centro_custos"].values
    # print(f"CC_DF {cc_ids}", flush=True)
    cc_report_status_df = model_to_dataframe(Update_cc_report_status)
    cc_report_status = cc_report_status_df["cc_id"].values
    # print(f"CC_REPORT_STATUS {cc_report_status}", flush=True)

    for ref_cc in cc_ids:
        # print(f"ref cc {ref_cc}", flush=True)
        if ref_cc in cc_report_status:
            ref = True
        else:
            # print(f"Registro que precisa ser inserido {ref_cc}", flush=True)
            create_new_update_status(ref_cc)


class CC_REPORT_MANAGER:
    def __init__(self):
        verify_cc_changes()

        self.update_report_status = UPDATE_EXTENSION_STATUS("CC_REPORT")
        # self.update_report_status.update_run_status(1)

    def update_cc_id_status(self, cc_id, type_ref):
        cc_manager = (
            db.session.query(Update_cc_report_status).filter_by(cc_id=cc_id).first()
        )

        if cc_manager is None:
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
        # print(f"ID {id}", flush=True)
        actual_day_date = get_current_date()
        url = f"https://app.vhsys.com.br/Relatorio/Relatorio.CentroCustos.JSON.php?considerarData=pagamento&Data1=01/01/2002&Data2={actual_day_date}&ListarCentroAtivoSemLancamento=1&modelo=2&Nome=&Cod=&Tipo={type}&Centro={id}&Categoria=null&buscar=1"
        return url

    def get_next_url(self):
        cc_report_status_df = model_to_dataframe(Update_cc_report_status)

        # Filter rows where either ENTRY or OUTPUT is 0
        filtered_df = cc_report_status_df[
            (cc_report_status_df["entries_runned"] == 0)
            | (cc_report_status_df["outputs_runned"] == 0)
        ]

        # Check if there are any rows matching the condition
        if not filtered_df.empty:
            # Select a random row from the filtered DataFrame
            random_row = filtered_df.sample()

            # Extract values from the random row
            CC_ID = random_row["cc_id"].values[0]
            ENTRY = random_row["entries_runned"].values[0]
            OUTPUT = random_row["outputs_runned"].values[0]

            # Determine whether to return an entry or output type based on which value is 0
            if ENTRY == 0:
                return {
                    "cc_id": CC_ID,
                    "url": self.get_url(CC_ID, "Entrada"),
                    "type": "entrada",
                }
            elif OUTPUT == 0:
                return {
                    "cc_id": CC_ID,
                    "url": self.get_url(CC_ID, "Saida"),
                    "type": "saida",
                }
        else:
            # Handle case when no rows match the condition
            print("No rows with ENTRY or OUTPUT equal to 0 found")

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
            # self.update_report_status.update_run_status(0)

        return {
            "running": running,
            "total_lines": total_lines,
            "number_of_entries": number_of_entries,
            "number_of_outputs": number_of_outputs,
        }
