from dataclasses import dataclass, field, fields
import enum
from typing import List


@dataclass
class Product:
    id: int
    name: str
    price: int
    scan_id: str
    keycode: str
    
    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


@dataclass
class Purchase:
    product: Product
    amount: int



@dataclass
class Basket:
    purchases: List[Purchase] = field(default_factory=list)

    @property
    def total(self):
        return sum(p.product.price * p.amount for p in self.purchases)

    def add(self, product, amount=1):
        for purchase in self.purchases:
            if purchase.product == product:
                purchase.amount += amount
                break
        else:
            self.purchases.append(Purchase(product, amount))

    def dict(self):
        return {
            "purchases": [
                {"product": purchase.product.id, "amount": purchase.amount}
                for purchase in self.purchases
            ]
        }

    def ui_format(self):
        options = []
        options.append((["", "", ""], -1))
        for i, purchase in enumerate(self.purchases):
            options.append(([
                purchase.product.name, 
                str(purchase.amount), 
                f"{purchase.amount*purchase.product.price/100:.2f}"
            ], i))
        options.append((["Total", "", f"{self.total/100:.2f}"], 1000))
        return options


@dataclass
class Catalog:
    products: List[Product] = field(default_factory=list)

    def search(self, data):
        data = data.lower().strip()

        for product in self.products:
            if product.scan_id.lower() == data:
                return [product]

        return [product for product in self.products if data in product.name.lower()]

    def keycode(self, code):
        return [product for product in self.products if code.lower() == product.keycode.lower()]

    @staticmethod
    def from_dict(dict):
        c = Catalog()
        for product in dict["products"]:
            c.products.append(Product(**product))
        return c
