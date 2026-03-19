import csv
import io
import os
import time
from datetime import datetime

import pytz
import requests
from dotenv import load_dotenv

load_dotenv()


class CloudLogger:
    def __init__(self, verbose=False):
        self.verbose = verbose
        if self.verbose:
            print("CloudLogger está pronto (modo verbose).")

        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.tenant_id = os.getenv("TENANT_ID")
        self.folder_path = os.getenv("ONEDRIVE_FOLDER_PATH")
        self.site_id = os.getenv("SHAREPOINT_SITE_ID")
        self.drive_id = os.getenv("SHAREPOINT_DRIVE_ID")

        # --- IMPROVEMENT ---
        # The log fields are now defined once when the logger is created.
        self.fieldnames = ["env", "service", "route", "action", "data"]

        if not all(
            [
                self.client_id,
                self.client_secret,
                self.tenant_id,
                self.site_id,
                self.drive_id,
            ]
        ):
            raise ValueError(
                "Ensure CLIENT_ID, SECRET, TENANT, SITE_ID, and DRIVE_ID are set in .env"
            )

        self.logs = []
        self.sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
        self.PORTUGUESE_MONTHS = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }
        self._access_token = None

    def _get_access_token(self):
        if self._access_token:
            return self._access_token
        if self.verbose:
            print("Requesting new access token...")
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        return self._access_token

    def add_log(self, log_data):
        new_log_entry = log_data.copy()
        new_log_entry["datetime"] = datetime.now(self.sao_paulo_tz).isoformat()
        self.logs.append(new_log_entry)

    # --- IMPROVEMENT ---
    # The 'fieldnames' argument is no longer needed here, making the call simpler.
    def upload_logs(self, year, month, clear_after_upload=True):
        if not self.logs:
            if self.verbose:
                print("\nNenhum log novo para fazer upload.")
            return

        try:
            token = self._get_access_token()
            month_name = self.PORTUGUESE_MONTHS.get(month)
            if not month_name:
                raise ValueError(f"Mês inválido: {month}")

            file_path_on_drive = f"/{self.folder_path}/{year}/{month_name}.csv"
            item_url = (
                f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}"
                f"/root:{file_path_on_drive}"
            )

            if self.verbose:
                print(f"Verificando arquivo existente em: {file_path_on_drive}...")
            past_logs = []
            headers = {"Authorization": f"Bearer {token}"}
            try:
                response = requests.get(item_url + ":/content", headers=headers)
                response.raise_for_status()
                past_logs = list(csv.DictReader(io.StringIO(response.text)))
            except requests.exceptions.HTTPError as e:
                if e.response.status_code != 404:
                    raise

            combined_logs = past_logs + self.logs
            output = io.StringIO()
            # It now uses self.fieldnames, defined in the constructor.
            updated_fieldnames = ["datetime"] + [
                fn for fn in self.fieldnames if fn != "datetime"
            ]
            writer = csv.DictWriter(output, fieldnames=updated_fieldnames)
            writer.writeheader()
            writer.writerows(combined_logs)

            if self.verbose:
                print(f"Fazendo upload de {len(combined_logs)} registros totais...")
            response = requests.put(
                item_url + ":/content",
                headers=headers,
                data=output.getvalue().encode("utf-8"),
            )
            response.raise_for_status()

            if self.verbose:
                print("Upload acumulativo bem-sucedido!")
            if clear_after_upload:
                self.logs.clear()
                if self.verbose:
                    print("Lista de logs interna foi limpa.")

        except Exception as e:
            print(f"Falha na operação: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response Body: {e.response.text}")


# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    # This constructor is now simpler
    logger = CloudLogger(verbose=True)

    # Add logs
    logger.add_log(
        {
            "env": "prod",
            "service": "Startup",
            "route": "N/A",
            "action": "Init",
            "data": "Logger initialized.",
        }
    )
    logger.add_log(
        {
            "env": "dev",
            "service": "Database",
            "route": "N/A",
            "action": "Connect",
            "data": "Connection successful.",
        }
    )

    # For today's date (August 25, 2025), this will save to "Agosto.csv"
    today = datetime.now()

    logger.upload_logs(year=today.year, month=today.month)
