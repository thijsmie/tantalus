from math import floor, ceil

from google.appengine.ext import ndb

import validate


class Relation(ndb.Model):
    name = ndb.StringProperty(required=True, validator=validate.ensurelength(4))
    budget = ndb.IntegerProperty(default=0)

    has_budget = ndb.BooleanProperty(required=True)
    send_mail = ndb.BooleanProperty(required=True)

    email = ndb.TextProperty(default="")


class Group(ndb.Model):
    name = ndb.StringProperty(required=True, validator=validate.ensurelength(4))


class Mod(ndb.Model):
    name = ndb.StringProperty(default="", required=True, validator=validate.ensurelength(4))
    tag = ndb.StringProperty(default="", required=True, validator=validate.ensurelength(1))
    description = ndb.TextProperty(default="")
    pre_add = ndb.IntegerProperty(default=0)
    multiplier = ndb.FloatProperty(default=0.0)
    post_add = ndb.IntegerProperty(default=0)
    modifies = ndb.BooleanProperty(default=False)
    divides = ndb.BooleanProperty(default=True)
    rounding = ndb.StringProperty(choices=["floor", "ceil", "round", "none"], required=True)

    def do_round(self, value):
        if self.rounding == "none":
            return value
        if self.rounding == "floor":
            return floor(value)
        if self.rounding == "ceil":
            return ceil(value)
        return round(value)

    def apply(self, line):
        if self.divides:
            price = self.do_round(
                (line.value + self.pre_add * line.amount) / self.multiplier + self.post_add * line.amount)
        else:
            price = self.do_round(
                (line.value + self.pre_add * line.amount) * self.multiplier + self.post_add * line.amount)

        price = int(price)
        diff = price - line.value
        if self.modifies:
            line.value = price

        line.mods.append(self.key)
        line.modamounts.append(int(diff))


class Product(ndb.Model):
    contenttype = ndb.StringProperty(required=True, validator=validate.ensurelength(4))
    tag = ndb.StringProperty(default="")
    value = ndb.IntegerProperty(default=0, validator=validate.ensurepositive())
    amount = ndb.IntegerProperty(default=0, validator=validate.ensurepositive())
    losemods = ndb.KeyProperty(Mod, repeated=True)
    gainmods = ndb.KeyProperty(Mod, repeated=True)

    hidden = ndb.BooleanProperty(default=False)
    group = ndb.KeyProperty(Group)

    def take(self, amount):
        if amount <= 0:
            raise validate.OperationError("Cannot take negative amount of {}!".format(self.contenttype))

        if amount > self.amount:
            raise validate.OperationError(
                "Taking {} but only {} of {} in stock".format(amount, self.amount, self.contenttype))

        value = int(round(self.value * amount / self.amount))
        self.amount -= amount
        self.value -= value

        return TransactionLine(
            product=self.key,
            amount=amount,
            value=value
        )

    def give(self, container):
        if container.product != self.key:
            raise validate.OperationError(
                "Cannot give {} to {}!".format(container.product.get().contenttype, self.contenttype))

        if container.amount < 0 or container.value < 0 or (
                            container.amount == 0 and self.amount == 0 and container.value > 0):
            raise validate.OperationError(
                "Adding {} to {} would create an invalid state!".format(str(container), str(self)))

        self.amount += container.amount
        self.value += container.value


class TransactionLine(ndb.Model):
    product = ndb.KeyProperty(kind=Product)

    modamounts = ndb.IntegerProperty(repeated=True)
    mods = ndb.KeyProperty(kind=Mod, repeated=True)
    value = ndb.IntegerProperty()
    amount = ndb.IntegerProperty()

    def take(self, amount):
        if amount <= 0:
            raise validate.OperationError("Cannot take negative amount!")

        if amount > self.amount:
            raise validate.OperationError(
                "Taking {} but only {} in stock".format(amount, self.amount))

        value = int(round(self.value * amount / self.amount))
        return TransactionLine(
            product=self.product,
            amount=amount,
            value=value
        )


class ServiceLine(ndb.Model):
    service = ndb.StringProperty()
    value = ndb.IntegerProperty()
    amount = ndb.IntegerProperty()


class Reference(ndb.Model):
    # Keys are the only thing guaranteed to be unique in a database. Set them as a combo Relation_refnumber
    # Also referred to as anit-race-condition magic
    pass


class Transaction(ndb.Model):
    reference = ndb.IntegerProperty()
    revision = ndb.IntegerProperty(default=0)
    reference_u = ndb.KeyProperty(kind=Reference)
    deliverydate = ndb.DateProperty()
    processeddate = ndb.DateProperty()
    lastedit = ndb.DateTimeProperty()
    description = ndb.TextProperty(default="")

    relation = ndb.KeyProperty(kind=Relation, required=True)

    one_to_two = ndb.LocalStructuredProperty(TransactionLine, repeated=True)
    two_to_one = ndb.LocalStructuredProperty(TransactionLine, repeated=True)
    services = ndb.LocalStructuredProperty(ServiceLine, repeated=True)

    total = ndb.IntegerProperty(default=0)


class User(ndb.Model):
    session = ndb.StringProperty()
    username = ndb.StringProperty(required=True, validator=validate.ensurelength(4))
    passhash = ndb.TextProperty(required=True)
    relation = ndb.KeyProperty(kind=Relation)

    right_admin = ndb.BooleanProperty(default=False)
    right_viewstock = ndb.BooleanProperty(default=False)
    right_viewalltransactions = ndb.BooleanProperty(default=False)
    right_posaction = ndb.BooleanProperty(default=False)

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
