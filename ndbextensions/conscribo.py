from google.appengine.ext import ndb
from ndbextensions.models import TypeGroup, Group, Relation, Transaction


class ConscriboGroupLink(ndb.Model):
    group = ndb.KeyProperty(kind=Group)
    linked = ndb.IntegerProperty(default=999)

    def __init__(self, *args, **kwargs):
        super(ConscriboGroupLink, self).__init__(*args, parent=TypeGroup.conscribo_ancestor(), **kwargs)

    @classmethod
    def get_by_group(cls, groupkey):
        return cls.query(cls.group == groupkey, ancestor=TypeGroup.conscribo_ancestor()).get()


class ConscriboRelationLink(ndb.Model):
    relation = ndb.KeyProperty(kind=Relation)
    linked = ndb.IntegerProperty(default=999)

    def __init__(self, *args, **kwargs):
        super(ConscriboRelationLink, self).__init__(*args, parent=TypeGroup.conscribo_ancestor(), **kwargs)

    @classmethod
    def get_by_relation(cls, relationkey):
        return cls.query(cls.relation == relationkey, ancestor=TypeGroup.conscribo_ancestor()).get()


class ConscriboTransactionLink(ndb.Model):
    transaction = ndb.KeyProperty(kind=Transaction)
    conscribo_reference = ndb.IntegerProperty()
    pushed_revision = ndb.IntegerProperty()
    bookdate = ndb.DateProperty()
    feedback = ndb.StringProperty(default="")

    def __init__(self, *args, **kwargs):
        super(ConscriboTransactionLink, self).__init__(*args, parent=TypeGroup.conscribo_ancestor(), **kwargs)

    @classmethod
    def get_by_transaction(cls, transactionkey):
        return cls.query(cls.transaction == transactionkey, ancestor=TypeGroup.conscribo_ancestor()).get()
