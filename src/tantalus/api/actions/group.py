from tantalus_db.base import db
from tantalus_db.models import Group


def get_group(name):
    if type(name) != str or len(name) < 4:
        raise Exception("Invalid group name")

    group = Group.query.filter(Group.name == name).first_or_none()

    if not group:
        group = Group(
            name=name
        )
        db.session.add(group)
    
    return group


def group_values():
    return {
        group.name: sum(product.amount * product.value for product in group.products)
            for group in Group.query.all()
    }