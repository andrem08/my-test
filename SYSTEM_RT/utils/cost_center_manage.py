import re

from models import Client_by_CC, db


def all_client_by_cc_ids():
    all_ids = db.session.query(Client_by_CC.CC).all()
    all_ids = [row[0] for row in all_ids]

    return all_ids


def extract_prefix(text):
    pattern = r"^[A-Z]{2}-[A-Z0-9]{3}"
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    else:
        return "-1"


def extract_cc_value(input_string):
    pattern = re.compile(r"CC[-\s]*(\d+)")
    match = pattern.search(input_string)
    if match:
        return int(match.group(1))
    else:
        return "-1"


def extract_cc_text_value(input_string):
    index = input_string.find("CC-")
    if index != -1:
        cc = input_string[index + 3 : index + 9]
        return cc
    else:
        return "-1"


def extract_cc_text_value_exceptions(string):
    string = string.replace("/", "")
    index = string.find("CC-")
    if index != -1:
        end_index = string.find("/", index)
        if end_index == -1:
            cc = string[index + 3 : index + 9]
        else:
            cc = string[index + 3 : end_index]
        return cc
    else:
        return "-1"


def get_cc_label(text):
    if text == "Vendas":
        return text
    if text == "Administração":
        return text
    label = extract_numeric_part(text)
    if label == "-1":
        label = extract_prefix(text)
        if label == "-1":
            label = extract_cc_value(text)
    return label


def extract_numeric_part(text):
    pattern = re.compile(r"\b(\d{6})\b")
    match = pattern.search(text)

    if match:
        return int(match.group(1))
    else:
        return "-1"


def cc_extract(text):
    extract = extract_numeric_part(text)
    if extract == -1:
        print("Extract")


class COST_CENTER_MANAGER:
    def __init__(self):
        self.all_ids = all_client_by_cc_ids()

    def verify_register_is_exist(self, id):
        if id in self.all_ids:
            return True
        else:
            return False

    def verify_CC_by_id_ref(self, cc_ref):
        if cc_ref == "-1":
            cc_ref = "NO-SET"
        result = self.verify_register_is_exist(cc_ref)
        if result is False:
            return "NO-SET"
        return cc_ref

    def get_cc_label(self, text):
        if text == "RT - Vendas":
            return "Vendas"
        if text == "Marketing":
            return "Marketing"
        if text == "Vendas":
            return text
        if text == "Administração":
            return text
        label = extract_cc_value(text)
        if label == "-1":
            label = extract_numeric_part(text)
            if label == "-1":
                label = extract_prefix(text)
                if label == "-1":
                    label = extract_cc_text_value(text)
                    if label == "-1":
                        label = extract_cc_text_value_exceptions(text)

        return label
