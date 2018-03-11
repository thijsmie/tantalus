from google.appengine.ext.ndb import Key, transactional
from ndbextensions.models import Referencing, Transaction, TransactionLine, ServiceLine
from ndbextensions.validate import OperationError
from ndbextensions.util import get_or_none

from api.actions.rows import transform_collection

from collections import defaultdict
from datetime import datetime
from pytz import timezone


@transactional(xg=True)
def new_transaction(data):
    reference = Referencing.get_reference()
    relation = get_or_none(data['Relation'])
    if relation is None:
        raise OperationError("Relation does not exist!")

    tr = Transaction.query(Transaction.relation == relation).order(-Transaction.informal_reference).get()
    if tr is None:
        informal_reference = 1
    else:
        informal_reference = tr.informal_reference + 1

    t = Transaction(
        revision=0,
        reference=reference,
        informal_reference=informal_reference,
        relation=relation.key,
        deliverydate=datetime.strptime(data["deliverydate"], "%Y-%m-%d").date(),
        processeddate=datetime.now(timezone("Europe/Amsterdam")).date(),
        description=data.get("description", "")
    )

    for prd in data["sell"]:
        product = get_or_none(prd["id"])
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))
        line = product.take(int(prd['amount']))
        product.put()

        t.one_to_two.append(line)

    for prd in data["buy"]:
        product = get_or_none(prd["id"])
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))
        line = TransactionLine(
            product=product.key,
            amount=int(prd['amount']),
            prevalue=int(prd['price']),
            value=product.value*int(prd['amount']),
            btwtype=product.btwtype
        )

        product.give(line)
        product.put()
        t.two_to_one.append(line)

    for prd in data["service"]:
        line = ServiceLine(
            service=prd['contenttype'],
            amount=int(prd['amount']),
            value=int(prd['price'])
        )

        t.services.append(line)

    t.total = transaction_total(t)
    t.put()
    return t


@transactional(xg=True)
def edit_transaction(t, data):
    # Easy stuff first
    # Note, this does not take care of money in budgets, do outside! Something with transactional limitations...
    t.revision += 1

    if "deliverydate" in data:
        t.deliverydate = datetime.strptime(data["deliverydate"], "%Y-%m-%d").date()

    if "description" in data:
        t.description = data["description"]

    newsell = []
    for prd in data["sell"]:
        product = get_or_none(prd["id"])
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))

        # We leave value at zero, will get filled in later
        line = TransactionLine(
            value=0,
            prevalue=0,
            amount=int(prd['amount']),
            product=product.key
        )

        newsell.append(line)

    t.one_to_two = transform_collection(t.one_to_two, newsell, True)

    newbuy = []
    for prd in data["buy"]:
        product = get_or_none(prd["id"])
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))
        line = TransactionLine(
            product=product.key,
            amount=int(prd['amount']),
            value=int(prd['price'])
        )

        newbuy.append(line)
    t.two_to_one = transform_collection(t.two_to_one, newbuy, False)

    t.services = []
    for prd in data["service"]:
        line = ServiceLine(
            service=prd['contenttype'],
            amount=int(prd['amount']),
            value=int(prd['price'])
        )

        t.services.append(line)

    record = transaction_record(t)
    t.total = record["total"]
    t.put()
    return t


def make_row_record(row):
    return {
        "contenttype": row.product.get().contenttype,
        "prevalue": row.prevalue,
        "value": row.value,
        "amount": row.amount,
        "btw": row.btwtype.get().percentage
    }


def make_service_record(row):
    return {
        "contenttype": row.service,
        "amount": row.amount,
        "prevalue": row.value
    }


def transaction_process(transaction):
    sellrows = [make_row_record(row) for row in transaction.one_to_two]
    buyrows = [make_row_record(row) for row in transaction.two_to_one]
    servicerows = [make_service_record(row) for row in transaction.services]

    btwtotals = defaultdict(float)
    if transaction.two_to_one_has_btw:
        if transaction.two_to_one_btw_per_row:
            # Current total including btw, btw rounded per row
            for row in buyrows:
                btw = round(row["prevalue"] * row["btw"] / 100 / (row["btw"] + 100))
                btwtotals[row["btw"]] += btw
                row["btwvalue"] = btw
        else:
            # Current total including btw, btw rounded for full invoice
            # We should use decimals here, but floats are good enough for now
            for row in buyrows:
                btw = row["prevalue"] * row["btw"] / 100 / (row["btw"] + 100)
                btwtotals[row["btw"]] += btw
                row["btwvalue"] = btw
    else:
        if transaction.two_to_one_btw_per_row:
            # Current total excluding btw, btw rounded per row
            for row in buyrows:
                btw = round(row["prevalue"] * row["btw"] / 100)
                btwtotals[row["btw"]] += btw
                row["btwvalue"] = btw
        else:
            # Current total excluding btw, btw rounded for full invoice
            # We should use decimals here, but floats are good enough for now
            for row in buyrows:
                btw = row["prevalue"] * row["btw"] / 100
                btwtotals[row["btw"]] += btw
                row["btwvalue"] = btw

    return dict(btwtotals), sellrows, buyrows, servicerows


def transaction_record(transaction):
    btwtotals, sellrows, buyrows, servicerows = transaction_process(transaction)

    total = sum([r['prevalue'] for r in sellrows]) - sum([r['prevalue'] for r in buyrows]) + sum(
        [r['prevalue'] for r in servicerows])

    if not transaction.two_to_one_has_btw:
        total -= sum(btwtotals.values())

    return {
        "reference": transaction.reference,
        "name": transaction.relation.get().name + " " + str(transaction.informal_reference).zfill(3),
        "sell": sellrows,
        "buy": buyrows,
        "service": servicerows,
        "description": transaction.description,
        "processeddate": transaction.processeddate,
        "deliverydate": transaction.deliverydate,
        "total": total,
        "id": transaction.key.urlsafe(),
        "revision": transaction.revision,
        "lastedit": transaction.lastedit
    }


