from math import floor, ceil

from google.appengine.ext import ndb

import validate


class TypeGroup(ndb.Model):
    @classmethod
    def product_ancestor(cls):
        return ndb.Key("Typegroup", "product")

    @classmethod
    def transaction_ancestor(cls):
        return ndb.Key("Typegroup", "transaction")

    @classmethod
    def relation_ancestor(cls):
        return ndb.Key("Typegroup", "relation")

    @classmethod
    def conscribo_ancestor(cls):
        return ndb.Key("Typegroup", "conscribo")
        

class Referencing(ndb.Model):
    counter = ndb.IntegerProperty(default=0)
    
    @classmethod
    def get_reference(cls):
        me = cls.get_or_insert("REF")
        me.counter += 1
        me.put()
        return me.counter
        

class Relation(ndb.Model):
    name = ndb.StringProperty(required=True, validator=validate.ensurelength(1))
    budget = ndb.IntegerProperty(default=0)

    has_budget = ndb.BooleanProperty(required=True)
    send_mail = ndb.BooleanProperty(required=True)
    numbered_reference = ndb.BooleanProperty(default=True)

    email = ndb.TextProperty(default="")
    address = ndb.TextProperty(default="")

    def __init__(self, *args, **kwargs):
        super(Relation, self).__init__(*args, parent=TypeGroup.relation_ancestor(), **kwargs)


class BtwType(ndb.Model):
    name = ndb.StringProperty(required=True, validator=validate.ensurelength(2))
    percentage = ndb.IntegerProperty(default=0, validator=validate.ensurepositive())

    def __init__(self, *args, **kwargs):
        super(BtwType, self).__init__(*args, parent=TypeGroup.product_ancestor(), **kwargs)
        
        
class Group(ndb.Model):
    name = ndb.StringProperty(required=True, validator=validate.ensurelength(4))

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, parent=TypeGroup.product_ancestor(), **kwargs)


class Product(ndb.Model):
    contenttype = ndb.StringProperty(required=True, validator=validate.ensurelength(4))
    tag = ndb.StringProperty(default="")
    value = ndb.IntegerProperty(default=0)
    amount = ndb.IntegerProperty(default=0)
    
    hidden = ndb.BooleanProperty(default=False)
    group = ndb.KeyProperty(Group)
    
    btwtype = ndb.KeyProperty(kind=BtwType)

    def take(self, amount):
        if amount <= 0:
            raise validate.OperationError("Cannot take negative amount of {}!".format(self.contenttype))

        self.amount -= amount
     
        return TransactionLine(
            product=self.key,
            amount=amount,
            prevalue=amount*self.value,
            value=amount*self.value,
            btwtype=self.btwtype
        )

    def give(self, container_or_amount):
        if type(container_or_amount) == int:
            amount = container_or_amount
        else:
            amount = container_or_amount.amount

        if amount < 0:
            raise validate.OperationError(
                "Cannot add a negative amount")

        self.amount += amount
        
    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, parent=TypeGroup.product_ancestor(), **kwargs)


class TransactionLine(ndb.Model):
    product = ndb.KeyProperty(kind=Product)
    
    prevalue = ndb.IntegerProperty()
    value = ndb.IntegerProperty()
    btwtype = ndb.KeyProperty(kind=BtwType)
    
    amount = ndb.IntegerProperty()

    def take(self, amount):
        if amount <= 0:
            raise validate.OperationError("Cannot take negative amount!")

        if amount > self.amount:
            raise validate.OperationError(
                "Taking {} but only {} in stock".format(amount, self.amount))

        # Note: this rounding is always precise
        value = self.value * amount // self.amount
        
        return TransactionLine(
            product=self.product,
            amount=amount,
            prevalue=value,
            btwtype=self.btwtype
        )


class ServiceLine(ndb.Model):
    service = ndb.StringProperty()
    value = ndb.IntegerProperty()
    amount = ndb.IntegerProperty()
    
    btwtype = ndb.KeyProperty(kind=BtwType)


class Transaction(ndb.Model):
    reference = ndb.IntegerProperty()
    informal_reference = ndb.IntegerProperty()
    revision = ndb.IntegerProperty(default=0)
    deliverydate = ndb.DateProperty()
    processeddate = ndb.DateProperty()
    lastedit = ndb.DateTimeProperty(auto_now=True)
    description = ndb.TextProperty(default="")

    relation = ndb.KeyProperty(kind=Relation, required=True)

    one_to_two = ndb.LocalStructuredProperty(TransactionLine, repeated=True)
    two_to_one = ndb.LocalStructuredProperty(TransactionLine, repeated=True)
    services = ndb.LocalStructuredProperty(ServiceLine, repeated=True)

    total = ndb.IntegerProperty(default=0)
    two_to_one_has_btw = ndb.BooleanProperty(default=False)
    two_to_one_btw_per_row = ndb.BooleanProperty(default=False)

    def __init__(self, *args, **kwargs):
        super(Transaction, self).__init__(*args, parent=TypeGroup.transaction_ancestor(), **kwargs)


class User(ndb.Model):
    session = ndb.StringProperty()
    username = ndb.StringProperty(required=True, validator=validate.ensurelength(4))
    passhash = ndb.TextProperty(required=True)
    relation = ndb.KeyProperty(kind=Relation)

    right_admin = ndb.BooleanProperty(default=False)
    right_viewstock = ndb.BooleanProperty(default=False)
    right_viewalltransactions = ndb.BooleanProperty(default=False)
    right_posaction = ndb.BooleanProperty(default=False)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, parent=TypeGroup.relation_ancestor(), **kwargs)

    # Flask-Login required functionality

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.session


class PosProduct(ndb.Model):
    product = ndb.KeyProperty(kind=Product)
    scan_id = ndb.StringProperty(default="")
    keycode = ndb.StringProperty(default="")

    name = ndb.StringProperty(default="")
    price = ndb.IntegerProperty(default=0)

    def __init__(self, *args, **kwargs):
        super(PosProduct, self).__init__(*args, parent=TypeGroup.product_ancestor(), **kwargs)


class PosSale(ndb.Model):
    product = ndb.KeyProperty(kind=PosProduct)
    amount = ndb.IntegerProperty(default=1)
    user = ndb.KeyProperty(kind=User)
    time = ndb.DateTimeProperty(auto_now_add=True)
    processed = ndb.BooleanProperty(default=False)

    def __init__(self, *args, **kwargs):
        super(PosSale, self).__init__(*args, parent=TypeGroup.product_ancestor(), **kwargs)
