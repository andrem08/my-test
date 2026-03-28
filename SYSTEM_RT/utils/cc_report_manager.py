def verify_all_cost_center_are_on_list():
    return -1


class COST_REPORT_MANAGER:
    # Classe que vai ser ultilizada junto com a nossa extensão para google chrome
    def __init__(self, CC_id, json_data):
        self.all_cost_center_ids = []
        self.CC_json_data = json_data
        self.CC_id = CC_id
        verify_all_cost_center_are_on_list()

    def get_cost_center_ids():
        print("Hello")

    def get_json_data_from_csv():
        print("Getting json data from csv")

    def get_cc_tokens(self, cc_id):
        return cc_id

    def process_report_by_cc(self, cc_id):
        return cc_id

    def verify_register_is_exist(self, id):
        if id in self.all_ids:
            # print(f"CC {id} alredy exist", flush=True)
            return True
        else:
            # print(f"CC {id} is new", flush=True)
            return False
