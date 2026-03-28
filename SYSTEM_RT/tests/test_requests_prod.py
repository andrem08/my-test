import os
import unittest

import requests
from dotenv import load_dotenv

load_dotenv()


class TestRequisitions(unittest.TestCase):
    def test_orders_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/orders/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_os_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/os/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_ov_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/ov/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    # def test_account_inputs_update(self):
    #     URL_REF = "https://systemrtdevazure.azurewebsites.net"
    #     route_ref = "/account_inputs/update"
    #     RT_TOKEN = os.getenv("RT_TOKEN")
    #     URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
    #     response = requests.put(URL)
    #     self.assertEqual(response.status_code, 201)

    def test_account_payment_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/account_payment/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_banks_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/banks/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_buy_order_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/buy_order/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        print(f"url {URL}")
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_category_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/category/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_cc_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/cc/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_cc_by_client_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/cc_by_client/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_client_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/client/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_clock_client_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/clock/clock_client/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_clock_entry_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/clock/clock_entry/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_clock_project_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/clock/clock_project/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_clock_user_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/clock/clock_user/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_clock_tags_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/clock/tags/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_contexted_hours_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/contexted_hours"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_extract_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/extract/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_merch_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/merch_entry"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_products_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/products"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_products_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/products"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_nf_update(self):
        URL_REF = "https://systemrtdevazure.azurewebsites.net"
        route_ref = "/nf/update"
        RT_TOKEN = os.getenv("RT_TOKEN")
        URL = f"{URL_REF}{route_ref}?rt_token={RT_TOKEN}"
        response = requests.put(URL)
        self.assertEqual(response.status_code, 201)

    def test_print_token(self):
        RT_TOKEN = os.getenv("RT_TOKEN")
        print(f"RT_TOKEN {RT_TOKEN}")


if __name__ == "__main__":
    unittest.main()
