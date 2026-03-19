import html
import logging
import re
import traceback
from collections import defaultdict

import xmltodict
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

from manage_employers import EMPLOYERS_MANAGE
from manageEmployersNew import EMPLOYERS_MANAGE_NEW
from manageEmployersCurrentStatus import EMPLOYERS_MANAGE_CURRENT_STATUS

employers = Blueprint("Employers", __name__)
load_dotenv()
logging.basicConfig(level=logging.INFO)


def transform_user_data(input_dict: dict) -> dict:
    dependentes = defaultdict(dict)
    beneficios = defaultdict(dict)
    global_data = {}

    pattern = re.compile(r"_(\d+)$")

    for key, value in input_dict.items():
        match = pattern.search(key)
        if not match:
            global_data[key] = value
            continue

        number = match.group(1)
        base_key = key[: match.start()]

        if "dependente" in base_key:
            dependentes[number][base_key] = value
        elif "beneficio" in base_key:
            beneficios[number][base_key] = value
    output = {
        **global_data,
        "dependentes": list(dependentes.values()),
        "beneficios": list(beneficios.values()),
    }
    return output


def decode_html_entities(data):
    if isinstance(data, dict):
        return {key: decode_html_entities(value) for key, value in data.items()}
    if isinstance(data, list):
        return [decode_html_entities(item) for item in data]
    if isinstance(data, str):
        return html.unescape(data)
    return data


@employers.route("/employers_general_data", methods=["POST"])
def employers_new():
  try:
    data = request.get_json()
    if not data:
      return (
        jsonify(
          {
            "error": "Invalid request. Missing JSON payload or incorrect Content-Type."
          }
        ),
        400,
      )
    current_data = data.get("data")
    current_data = current_data.get("source")
    current_data = current_data.get("itens")
    # print(f"\n \n Employer general data {current_data}")
    
    manage_current_status = EMPLOYERS_MANAGE_CURRENT_STATUS(current_data)
    manage_current_status.get_updates()


    return (
      jsonify(
        {"status": "success", "message": "Employers general data processed successfully."}
      ),
      201,
    )

  except Exception:
    logging.error(f"Error in /employers endpoint: {traceback.format_exc()}")
    return jsonify({"error": "An internal server error occurred."}), 500


@employers.route("/employers_plus", methods=["POST"])
def employers_extract_codes():
    try:
        data = request.get_json()
        xml_string = data.get("xml_ref") if data else None

        if not xml_string:
            return (
                jsonify({"error": "Request must be JSON with an 'xml_ref' key."}),
                400,
            )

        cdata_match = re.search(r"<!\[CDATA\[(.*?)\]\]>", xml_string, re.DOTALL)
        if not cdata_match:
            return (
                jsonify({"error": "No CDATA section found in the provided XML."}),
                400,
            )

        html_content = cdata_match.group(1).strip()
        soup = BeautifulSoup(html_content, "lxml")

        rows = soup.find_all("tr", class_="table-row-body")
        if not rows:
            return (
                jsonify({"error": "No table rows with class 'table-row-body' found."}),
                404,
            )

        extracted_data = [
            {"codigo": row.get("codigo")} for row in rows if row.get("codigo")
        ]

        logging.info(
            f"Extracted {len(extracted_data)} codes from /employers_plus endpoint."
        )
        return (
            jsonify(
                {
                    "message": "Employee codes extracted successfully.",
                    "ids": extracted_data,
                }
            ),
            200,
        )

    except Exception:
        logging.error(f"Error in /employers_plus endpoint: {traceback.format_exc()}")
        return (
            jsonify({"error": "An internal server error occurred while parsing data."}),
            500,
        )


@employers.route("/employers_plus_info", methods=["POST"])
def employers_process_info():
    try:
        data = request.get_json()
        xml_string = data.get("xml_ref") if data else None

        if not xml_string:
            return (
                jsonify({"error": "Request must be JSON with an 'xml_ref' key."}),
                400,
            )

        xml_dict = xmltodict.parse(xml_string)

        cmd_items = xml_dict.get("xjx", {}).get("cmd", [])
        if not cmd_items:
            return jsonify({"error": "XML must contain a <xjx><cmd> structure."}), 400

        info_dict_ref = {
            item.get("@t"): item.get("#text") for item in cmd_items if item.get("@t")
        }

        transformed_info_dict = transform_user_data(info_dict_ref)

        logging.info(
            f"Processing detailed info for employer: {transformed_info_dict.get('nome_funcionario')}"
        )

        emp_manage_new = EMPLOYERS_MANAGE_NEW(transformed_info_dict)
        emp_manage_new.get_updates()

        return (
            jsonify(
                {
                    "message": "Data processed and saved successfully.",
                    "transformed_data": transformed_info_dict,
                }
            ),
            201,
        )

    except Exception:
        logging.error(
            f"Error in /employers_plus_info endpoint: {traceback.format_exc()}"
        )
        return jsonify({"error": "An internal server error occurred."}), 500