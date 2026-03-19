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
    # Define a regular expression pattern to find the value after "CC-" or "CC "
    pattern = re.compile(r"CC[-\s]*(\d+)")

    # Search for the pattern in the input string
    match = pattern.search(input_string)

    # If a match is found, return the matched value as an integer
    if match:
        return int(match.group(1))
    else:
        # If no match is found, return -1
        return "-1"


def extract_cc_text_value(input_string):
    # Define a regular expression pattern to find the value after "CC-" or "CC "
    index = input_string.find("CC-")  # Find the index of "CC-"
    if index != -1:  # If "CC-" is found
        cc = input_string[index + 3 : index + 9]  # Extract 6 characters after "CC-"
        return cc
    else:
        return "-1"  # Return None if "CC-" is not found


def extract_cc_text_value_exceptions(string):
    string = string.replace("/", "")  # Remove all forward slashes from the string
    index = string.find("CC-")  # Find the index of "CC-"
    if index != -1:  # If "CC-" is found
        end_index = string.find("/", index)  # Find the index of "/" after "CC-"
        if (
            end_index == -1
        ):  # If "/" is not found, take characters until the end of the string
            cc = string[index + 3 : index + 9]  # Extract 6 characters after "CC-"
        else:  # If "/" is found, take characters until "/"
            cc = string[
                index + 3 : end_index
            ]  # Extract characters after "CC-" until "/"
        return cc
    else:
        return "-1"  # Return None if "CC-" is not found


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


# Esta função verifica e


##Extract from the first digits
def extract_numeric_part(text):
    pattern = re.compile(r"\b(\d{6})\b")
    match = pattern.search(text)

    if match:
        return int(match.group(1))
    else:
        return "-1"


# Global function to extract os cost_center and verify if there is a valid one option
def cc_extract(text):
    extract = extract_numeric_part(text)
    if extract == -1:
        print("Extract")


class COST_CENTER_MANAGER:
    def __init__(self):
        self.all_ids = all_client_by_cc_ids()

    def verify_register_is_exist(self, id):
        if id in self.all_ids:
            # print(f"CC {id} alredy exist", flush=True)
            return True
        else:
            # print(f"CC {id} is new", flush=True)
            return False

    def verify_CC_by_id_ref(self, cc_ref):
        # print(f" CC_REF HERE {cc_ref}", flush=True)
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
            #print(f"Level 1 {text} {label}", flush=True)
            label = extract_numeric_part(text)
            if label == "-1":
                #print(f"Level 2  {text} {label}", flush=True)
                label = extract_prefix(text)
                if label == "-1":
                    #print(f"Level 3 {text} {label}", flush=True)
                    label = extract_cc_text_value(text)
                    if label == "-1":
                        label = extract_cc_text_value_exceptions(text)
                        #print(f"Level 4 {text} {label}", flush=True)
        # print(
        #     f" \n \n \n Aqui esta a nossa label final {label}",
        #     flush=True,
        # )

        return label
