"""
Utilities for generating invoices for point-of-sale endpoints
"""

from tantalus_db.base import db
from tantalus_db.models import Transaction, PosSale, Product, ServiceLine, TransactionLine, Referencing
from tantalus_db.utility import transactional

from tantalus.api.actions.btwtype import get_btwtype

from datetime import datetime, timezone
from collections import defaultdict


@transactional
def make_pos_transaction(endpoint, begin_date, end_date):
    relation = endpoint.relation
    time_begin = datetime.combine(begin_date, datetime.min.time())
    time_end = datetime.combine(end_date, datetime.max.time())

    sales = PosSale.query.filter(
        PosSale.time_created >= time_begin,     
        PosSale.time_created <= time_end,
        PosSale.endpoint == endpoint,
        PosSale.processed == False
    ).all()

    service_amount = defaultdict(int)
    product_amount = defaultdict(int)

    # By using these weird keys (tuples are hasable)
    # we maintain full compatibility with price&btw changes at any time
    for sale in sales:
        if sale.posproduct.is_service:
            key = (sale.posproduct.service, sale.unit_price, sale.btwtype.percentage)
            service_amount[key] += sale.amount
        else:
            key = (sale.posproduct.product_id, sale.unit_price, sale.btwtype.percentage)
            product_amount[key] += sale.amount

    total = 0

    service_lines = []
    for (service, unit_price, btw), amount in service_amount.items():
        service_lines.append(ServiceLine(
            service=service,
            value=unit_price * amount,
            amount=amount,
            btwtype=get_btwtype(btw)
        ))
        total += unit_price * amount

    sell_lines = []
    for (product_id, unit_price, btw), amount in product_amount.items():
        product = Product.query.get(product_id)
        product.amount -= amount

        sell_lines.append(TransactionLine(
            product=product,
            prevalue=unit_price * amount,
            value=unit_price * amount,
            amount=amount,
            btwtype=get_btwtype(btw)
        ))
        total += unit_price * amount

    if relation.numbered_reference:
        reference = Referencing.get_reference()
    else:
        reference = 0        

    tr = Transaction.query.filter(Transaction.relation == relation).order_by(
        Transaction.informal_reference.desc()).first()

    if tr is None:
        informal_reference = 1
    else:
        informal_reference = tr.informal_reference + 1

    transaction = Transaction(
        reference = reference,
        informal_reference = informal_reference,
        deliverydate = end_date,
        processeddate = datetime.now(timezone("Europe/Amsterdam")).date(),
        description = "POS sales between {} and {} for endpoint {}.".format(
            begin_date.strftine("%Y-%m-%d"), end_date.strftine("%Y-%m-%d"), endpoint.name
        ),
        relation= relation,
        one_to_two= sell_lines,
        two_to_one = [],
        services = service_lines,
        total = total
    )
    db.session.add(transaction)

    for sale in sales:
        sale.processed = True