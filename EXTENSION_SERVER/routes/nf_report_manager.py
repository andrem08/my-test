import hashlib
import html
import re

import pandas as pd
import xmltodict
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

from cost_center_manager import COST_CENTER_MANAGER
from manage_sales_nf_report import SALES_NF_REPORT_MANAGE
from manage_service_nf_report import SERVICE_NF_REPORT_MANAGE
from models import NF_ServiceMetadata, db
from service_nf_manager import SERVICE_NF_MANAGER
from service_nf_metadata_manager import SERVICE_NF_METADATA_MANAGER, model_to_dicts

nf_report_manager = Blueprint("NF_REPORT_MANAGER", __name__)

load_dotenv()


def clean_cell(value):
    if isinstance(value, str):
        # Remove both escaped \n, \t and actual \n, \t characters
        cleaned_value = re.sub(
            r"\\n|\\t|\n|\t|\r+", " ", value
        )  # Remove any sequence of \n, \t, and \r (both escaped and non-escaped)

        # Replace multiple spaces with a single space and strip leading/trailing spaces
        cleaned_value = re.sub(r"\s+", " ", cleaned_value).strip()

        # print(f"Cleaned value: {repr(cleaned_value)}")  # For debugging purposes
        return cleaned_value
    return value  # Return the value unchanged if it's not a string


# Function to clean the HTML content
def clean_html_content(html_content):
    # Remove newline characters and tabs globally
    html_content = re.sub(r"[\n\t\r]+", " ", html_content)
    # Replace multiple spaces with a single space
    html_content = re.sub(r"\s+", " ", html_content)
    return html_content.strip()  # Remove leading/trailing whitespace


def clean_dict(data_dict):
    cleaned_dict = {}

    for key, value in data_dict.items():
        # Check if the value is a string
        if isinstance(value, str):
            # Remove escape sequences like \", \n, \t, \\, and extra spaces
            cleaned_value = re.sub(r"\\[\"ntr]", "", value)  # remove \", \n, \t, \r
            cleaned_value = cleaned_value.strip()  # remove leading and trailing spaces
        elif isinstance(value, list):
            # Clean items in the list
            cleaned_value = [re.sub(r"\\[\"ntr]", "", item).strip() for item in value]
        else:
            cleaned_value = value

        cleaned_dict[key] = cleaned_value

    return cleaned_dict


def extract_table_data(html_content):
    try:
        soup = BeautifulSoup(html_content, "lxml")
        table = soup.find("table")
        if not table:
            return {"error": "Table not found"}

        rows = table.find_all("tr")
        table_data = []

        for row in rows:
            tr_dict = clean_dict(row.attrs)

            table_ref = {
                "codigo": tr_dict.get("codigo"),
                "contas": tr_dict.get("contas"),
                "boletos": tr_dict.get("boletos"),
                "nota": tr_dict.get("nota"),
                "cliente": tr_dict.get("cliente"),
                "status": tr_dict.get("status"),
                "vendedor": tr_dict.get("vendedor"),
                "chave": tr_dict.get("chave"),
                "numeronfs": tr_dict.get("numeronfs"),
                "notarecibo": tr_dict.get("notarecibo"),
                "vinculooscomnfs": tr_dict.get("vinculooscomnfs"),
            }
            table_data.append(table_ref)

        return table_data

    except Exception as e:
        return {"error": str(e)}


def generate_id_token(seed):
    """Generates a unique SHA-256 hash based on a seed string."""
    return hashlib.sha256(seed.encode()).hexdigest()


def decode_html_entities(data):
    """Recursively decodes HTML entities in strings, lists, and dictionaries."""
    if isinstance(data, dict):
        return {key: decode_html_entities(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [decode_html_entities(item) for item in data]
    elif isinstance(data, str):
        return html.unescape(data)
    else:
        return data


@nf_report_manager.route("/sales_nf_report", methods=["POST"])
def sales_new_entry_by_id():
    """Handles new entries for sales NF reports."""
    try:
        data = request.get_json()
        decoded_data = decode_html_entities(data)
        # print(f" RAW DATA FORM SALE REPORT  {data}")
        payload_data = decoded_data["data"]["source"]["itens"]
        print(f"Payload data {payload_data}")
        sales_nf_report_manager = SALES_NF_REPORT_MANAGE(payload_data)
        sales_nf_report_manager.get_updates()
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "GET A NEW regular_bills status "}), 201


@nf_report_manager.route("/service_nf_report", methods=["POST"])
def service_new_entry_by_id():
    """Handles new entries for service NF reports."""
    try:
        data = request.get_json()
        decoded_data = decode_html_entities(data)
        payload_data = decoded_data["data"]["source"]["itens"]
        service_nf_report_manager = SERVICE_NF_REPORT_MANAGE(payload_data)
        service_nf_report_manager.get_updates()
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "GET A NEW regular_bills status "}), 201


@nf_report_manager.route("/nf_service_labels", methods=["POST"])
def get_nf_service_labels():
    try:

        raw_html = request.data.decode("utf-8")  # Decode raw HTML
        html_content_match = re.search(r"<!\[CDATA\[(.*?)\]\]>", raw_html, re.DOTALL)
        html_content = html_content_match.group(1).strip()
        extract_data = extract_table_data(html_content)
        # print("Extracted data", extract_data)
        df = pd.DataFrame.from_dict(extract_data)
        # print("Dataframe", df)
        service_metadata_nf_manager = SERVICE_NF_METADATA_MANAGER(df)
        service_metadata_nf_manager.get_updates()
        return (
            jsonify(
                {
                    "message": "Data extracted, cleaned, and converted to DataFrame successfully",
                    # "data": extracted_data,
                }
            ),
            200,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@nf_report_manager.route("/nf_service_labels_ids", methods=["GET"])
def get_nf_service_labels_ids():
    try:

        service_nf_metadata_ids = model_to_dicts(
            NF_ServiceMetadata, ["codigo", "numeronfs"]
        )
        return (
            jsonify(
                {
                    "status": "Manager status id",
                    "data": service_nf_metadata_ids,
                }
            ),
            200,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@nf_report_manager.route("/nf_service_info", methods=["POST"])
def get_nf_service_info():
    try:
        CC_MANAGER = COST_CENTER_MANAGER()

        data = request.get_json()
        xml_string = data.get("xml_ref", "")
        if not xml_string:
            return jsonify({"error": "No XML data provided"}), 400
        xml_dict = xmltodict.parse(xml_string)
        xml_data_ref = xml_dict["xjx"]["cmd"]
        info_dict_ref = {}
        for item in xml_data_ref:
            label = item.get("@t", "no-set")
            value = item.get("#text", "no-set")
            info_dict_ref[label] = clean_cell(value)

        # print("Data", data)
        del info_dict_ref["no-set"]
        del info_dict_ref["estoque_pedido"]
        del info_dict_ref["bloquear_edicao_cliente"]
        info_dict_ref["cc_ref"] = (
            CC_MANAGER.get_cc_label(info_dict_ref["obs_interno_pedido"]),
        )
        # print("Info dict ref", info_dict_ref)
        dict_array = [info_dict_ref]
        df = pd.DataFrame.from_dict(dict_array)
        service_nf_manager = SERVICE_NF_MANAGER(df)
        service_nf_manager.get_updates()
        return (
            jsonify(
                {
                    "message": "Data extracted, cleaned, and converted to DataFrame successfully",
                }
            ),
            200,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
