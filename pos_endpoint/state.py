from enum import Enum, auto
from .basket import Catalog, Basket
import logging


class ClientState(Enum):
    Initial = auto()
    Shopping = auto()
    Cancel = auto()
    Purchase = auto()
    Error = auto()
    Fatal = auto()


class ClientStateHolder:
    def __init__(self):
        self.state = ClientState.Initial

        self.session = None
        self.basket = None
        self.catalog = None

    def transition_initial_shopping(self, session):
        assert self.state == ClientState.Initial

        try:
            self.session = session
            self.basket = Basket()
            self.catalog = Catalog.from_dict(session.get_catalog_data())
            self.state = ClientState.Shopping
        except Exception as e:
            logging.critical(e)
            self.state = ClientState.Fatal

    def transition_shopping_cancel(self):
        assert self.state == ClientState.Shopping

        try:
            self.basket = None
            self.state = ClientState.Cancel
        except Exception as e:
            logging.error(e)
            self.state = ClientState.Error

    def transition_cancel_shopping(self):
        assert self.state == ClientState.Cancel

        try:
            self.basket = Basket()
            self.state = ClientState.Shopping
        except Exception as e:
            logging.error(e)
            self.state = ClientState.Error

    def transition_shopping_purchase(self):
        assert self.state == ClientState.Shopping

        try:
            self.session.submit_basket(self.basket)
            self.state = ClientState.Purchase
        except Exception as e:
            logging.error(e)
            self.state = ClientState.Error

    def transition_purchase_shopping(self):
        assert self.state == ClientState.Purchase

        try:
            self.basket = Basket()
            self.state = ClientState.Shopping
        except Exception as e:
            logging.error(e)
            self.state = ClientState.Error

    def transition_error_initial(self):
        assert self.state == ClientState.Error

        self.session = None
        self.basket = None
        self.catalog = None
        self.state = ClientState.Initial

