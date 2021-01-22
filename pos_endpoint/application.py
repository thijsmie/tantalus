from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from .state import ClientStateHolder
from .session import Session


class TextActionType(Enum):
    Nothing = 0
    SearchResults = 1
    BasketRefresh = 2
    Feedback = 3
    Shutdown = 4


@dataclass
class TextAction:
    action_type: TextActionType
    content: Any = None


class Application:
    def __init__(self, config):
        self.config = config
        self.state = ClientStateHolder()
        self.session = Session(config)
        self.state.transition_initial_shopping(self.session)
        self.retain_amount = None

    @property
    def basket(self):
        return self.state.basket

    @property
    def catalog(self):
        return self.state.catalog

    def text_action(self, text):
        if text == "":
            if self.basket.purchases:
                self.state.transition_shopping_purchase()
                self.state.transition_purchase_shopping()
                return TextAction(TextActionType.BasketRefresh), TextAction(TextActionType.Feedback, "Transaction successful")
            else:
                return TextAction(TextActionType.Nothing),

        results = self.catalog.search(text)
        
        if not results:
            return TextAction(TextActionType.Nothing),

        if len(results) == 1:
            self.basket.add(results[0])
            return TextAction(TextActionType.BasketRefresh),

        return TextAction(TextActionType.SearchResults, results),

    def keycode_action(self, text, code):
        results = self.catalog.keycode(code)

        if not results:
            return TextAction(TextActionType.Nothing),

        amount = 1
        try:
            amount = int(text)
        except:
            pass

        if len(results) == 1:
            self.basket.add(results[0], amount=amount)
            return TextAction(TextActionType.BasketRefresh),

        self.retain_amount = amount
        return TextAction(TextActionType.SearchResults, results),

    def search_submit(self, product):
        self.basket.add(product, self.retain_amount)
        self.retain_amount = None
        return TextAction(TextActionType.BasketRefresh),

    def search_cancel(self):
        self.retain_amount = None
        return TextAction(TextActionType.Nothing),
