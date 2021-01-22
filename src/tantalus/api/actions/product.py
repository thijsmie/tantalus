from tantalus_db.base import db
from tantalus_db.models import Product, Group, BtwType
from tantalus_db.utility import transactional

from tantalus.api.actions.group import get_group
from tantalus.api.actions.btwtype import get_btwtype

import logging


@transactional
def new_product(data):
    group = get_group(data['group'])
    btwtype = get_btwtype(data['btw'])

    product = Product(
        contenttype=data['name'],
        tag=data.get('tag', ''),
        group=group,
        amount=int(data.get('amount', 0)),
        value=int(data.get('value', 0)),
        discontinued=False,
        btwtype=btwtype
    )
    db.session.add(product)
    
    return product

@transactional
def edit_product(product, data):
    group = get_group(data['group']) if 'group' in data else product.group
    btwtype = get_btwtype(data['btw']) if 'btwtype' in data else product.btwtype

    product.group = group
    product.btwtype = btwtype

    product.contenttype = data.get('name', product.contenttype)
    product.tag = data.get('tag', product.tag)
    product.amount = int(data.get('amount', product.amount))
    product.value = int(data.get('value', product.value))

    return product

