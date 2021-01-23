from tantalus_db.base import db
from tantalus_db.models import Relation
from tantalus_db.utility import transactional


@transactional
def new_relation(data):
    relation = Relation(
        name=data['name'],
        budget=data['budget'],
        email=data['email'],
        has_budget=data['has_budget'],
        send_mail=data['send_mail'],
        address=data['address'],
        numbered_reference=data['reference']
    )
    db.session.add(relation)
    return relation


@transactional
def edit_relation(relation, data):
    relation.name = data.get('name', relation.name)
    relation.budget = data.get('budget')
    relation.email = data.get('email')
    relation.has_budget = data.get('has_budget')
    relation.send_mail = data.get('send_mail')
    relation.address = data.get('address')
    relation.numbered_reference = data.get('reference')

    return relation