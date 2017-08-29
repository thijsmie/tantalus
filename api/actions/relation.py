from google.appengine.ext.ndb import transactional


@transactional()
def add_to_budget(relation_key, amount):
    relation = relation_key.get()
    if relation.has_budget:
        relation.budget += amount
        relation.put()
