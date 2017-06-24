from holdmybeer.core import Bucket
from holdmybeer.complex import RatioBucket, Bucketlist, Stream

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import messages

from math import floor, ceil


class Party(ndb.Model):
    name = ndb.StringProperty()
    isme = ndb.BooleanProperty()
    budget = ndb.IntegerProperty()

    email = ndb.TextProperty()


class User(ndb.Model):
    username = ndb.StringProperty()
    passhash = ndb.TextProperty()
    party = ndb.KeyProperty(kind=Party)

    right_viewstock = ndb.BooleanProperty(default=False)
    right_viewalltransactions = ndb.BooleanProperty(default=False)
    right_posaction = ndb.BooleanProperty(default=False)


class Rounding(messages.Enum):
    NONE = -1
    FLOOR = 0
    CEIL = 1
    ROUND = 2

    @staticmethod
    def apply(rounding, value):
        if rounding == Rounding.NONE:
            return value
        elif rounding == Rounding.FLOOR:
            return floor(value)
        elif rounding == Rounding.CEIL:
            return ceil(value)
        elif rounding == Rounding.ROUND:
            return round(value)


class Group(ndb.Model):
    name = ndb.StringProperty()


class Mod(ndb.Model):
    name = ndb.StringProperty()
    tag = ndb.StringProperty()
    description = ndb.TextProperty()
    pre_add = ndb.IntegerProperty()
    multiplier = ndb.FloatProperty()
    post_add = ndb.IntegerProperty()
    included = ndb.BooleanProperty()
    rounding = msgprop.EnumProperty(Rounding)


class Product(ndb.Model, Bucket):
    contenttype = ndb.StringProperty()
    value = ndb.IntegerProperty()
    amount = ndb.IntegerProperty()

    value_constant = ndb.BooleanProperty()
    losemods = ndb.StructuredProperty(Mod, repeated=True)
    gainmods = ndb.StructuredProperty(Mod, repeated=True)

    hidden = ndb.BooleanProperty()
    group = ndb.KeyProperty(kind=Group)


class Warehouse(Bucketlist):
    """This is an awesome cheat. Make the entire inventory catalogue available as computed property."""
    singletype = Product
    autocreate = False  # Do not magically spawn new products
    makemydict = False  # Prevents default initializer to act on these objects

    @property
    def mydict(self):
        return self

    def __getitem__(self, item):
        return Product.query(contenttype=item)

    def __contains__(self, item):
        return Product.query(contenttype=item) is not None


class TransactionLine(ndb.Model, Bucket):
    product = ndb.KeyProperty(kind=Product)

    prevalue = ndb.IntegerProperty()
    value = ndb.IntegerProperty()
    amount = ndb.IntegerProperty()

    @property
    def contenttype(self):
        return self.product.get().contenttype


class Collection(ndb.Model, Bucketlist):
    singletype = TransactionLine
    autocreate = True
    makemydict = False
    mylist = ndb.StructuredProperty(TransactionLine, repeated=True)

    @property
    def mydict(self):
        return self

    def __getitem__(self, item):
        for c in self.mylist:
            if item == c.contenttype:
                return c
        raise KeyError(item)

    def __contains__(self, item):
        for c in self.mylist:
            if item == c.contenttype:
                return True
        return False


class Transaction(ndb.Model, Stream):
    listtype = Collection

    reference = ndb.StringProperty()
    deliverydate = ndb.DateProperty()
    processeddate = ndb.DateProperty()

    one = ndb.KeyProperty(kind=Party)
    two = ndb.KeyProperty(kind=Party)

    one_to_two = ndb.StructuredProperty(Collection, repeated=False)
    two_to_one = ndb.StructuredProperty(Collection, repeated=False)


class Recipe(ndb.Model, RatioBucket):
    listtype = Warehouse
    singletype = Product

    contenttype = ndb.StringProperty()
    ratios = ndb.JsonProperty(json_type=dict)
