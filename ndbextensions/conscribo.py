from google.appengine.ext import ndb
from ndbextensions.models import TypeGroup, Group, Relation, Transaction
import json


class ConscriboConfig(ndb.Model):
    config = ndb.StringProperty(default="{}")

    @classmethod
    def get_config(cls):
        return json.loads(cls.get_or_insert("CONSCRIBO").config)

    @classmethod
    def set_config(cls, config):
        inst = cls.get_or_insert("CONSCRIBO")
        inst.config = json.dumps(config)
        inst.put()

    @classmethod
    def default_config(cls):
        from ndbextensions.models import Group, Relation, BtwType
        groups = Group.query().fetch()
        relations = Relation.query().fetch()
        types = BtwType.query().fetch()

        return {
            "todo": 999,
            "groups": {g.name: {"inventory": 999, "profit": 999} for g in groups},
            "relations": {r.name: 999 for r in relations},
            "vatcodes": {str(t.percentage): "0" for t in types}
        }


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
