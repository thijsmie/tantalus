from .basket import Catalog, Product

import getpass
import requests


class Session:
    def __init__(self, config):
        s = requests.session()

        username = config.username or input("Username: ")
        password = config.password or getpass.getpass("Password: ")
        endpoint = config.endpoint or input("Endpoint: ")

        r = s.post(config.url("login"), json={"username": username, "password": password})
        r.raise_for_status()

        del password
        self.session = s
        self.config = config
        self.endpoint = endpoint

    def stop(self):
        self.session.get(self.config.url("logout"))
        self.session.close()

    def load_endpoints(self):
        r = self.session.get(self.config.url("products"))
        r.raise_for_status()
        return r.json()["endpoints"]

    def get_catalog_data(self):
        r = self.session.get(self.config.url("products"))
        r.raise_for_status()
        return r.json()

    def submit_basket(self, basket):
        for purchase in basket.purchases:
            self.sell(purchase.product.id, purchase.amount)

    def sell(self, product, amount):
        r = self.session.post(self.config.url("sell"), json={"product": product, "endpoint": self.endpoint, "amount": amount})
        r.raise_for_status()
        return r.json()["sale"]
        
