from google.appengine.ext.ndb import transactional
from ndbextensions.models import Referencing, Transaction, TransactionLine, ServiceLine, Relation, Product, TypeGroup
from ndbextensions.validate import OperationError
from ndbextensions.utility import get_or_none

from api.actions.rows import transform_collection

from collections import defaultdict
from datetime import datetime
from pytz import timezone


@transactional(xg=True)
def new_transaction(data):
    reference = Referencing.get_reference()
    relation = get_or_none(data['relation'], Relation)
    if relation is None:
        raise OperationError("Relation does not exist!")

    tr = Transaction.query(Transaction.relation == relation.key, ancestor=TypeGroup.transaction_ancestor()).order(
        -Transaction.informal_reference).get()
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
        product = get_or_none(prd["id"], Product)
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))
        line = product.take(int(prd['amount']))
        product.put()

        t.one_to_two.append(line)

    for prd in data["buy"]:
        product = get_or_none(prd["id"], Product)
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))
        line = TransactionLine(
            product=product.key,
            amount=int(prd['amount']),
            prevalue=int(prd['price']),
            value=product.value * int(prd['amount']),
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

    rec = transaction_record(t)
    t.total = rec["total"]
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
        product = get_or_none(prd["id"], Product)
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))

        line = TransactionLine(
            value=int(prd['amount'])*product.value,
            prevalue=int(prd['amount'])*product.value,
            amount=int(prd['amount']),
            product=product.key,
            btwtype=product.btwtype
        )

        newsell.append(line)

    t.one_to_two = transform_collection(t.one_to_two, newsell, True)

    newbuy = []
    for prd in data["buy"]:
        product = get_or_none(prd["id"], Product)
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))
        line = TransactionLine(
            product=product.key,
            amount=int(prd['amount']),
            prevalue=int(prd['price']),
            value=int(prd['amount'])*product.value,
            btwtype=product.btwtype
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

    sellbtwtotals = defaultdict(float)
    # Current total including btw, btw rounded per invoice
    for row in sellrows:
        btw = row["prevalue"] * row["btw"] / 100 / (row["btw"] + 100)
        sellbtwtotals[row["btw"]] += btw
        row["btwvalue"] = btw

    buybtwtotals = defaultdict(float)
    if transaction.two_to_one_has_btw:
        if transaction.two_to_one_btw_per_row:
            # Current total including btw, btw rounded per row
            for row in buyrows:
                btw = round(row["prevalue"] * row["btw"] / 100 / (row["btw"] + 100))
                buybtwtotals[row["btw"]] += btw
                row["btwvalue"] = btw
        else:
            # Current total including btw, btw rounded for full invoice
            # We should use decimals here, but floats are good enough for now
            for row in buyrows:
                btw = row["prevalue"] * row["btw"] / 100 / (row["btw"] + 100)
                buybtwtotals[row["btw"]] += btw
                row["btwvalue"] = btw
    else:
        if transaction.two_to_one_btw_per_row:
            # Current total excluding btw, btw rounded per row
            for row in buyrows:
                btw = round(row["prevalue"] * row["btw"] / 100)
                buybtwtotals[row["btw"]] += btw
                row["btwvalue"] = btw
        else:
            # Current total excluding btw, btw rounded for full invoice
            # We should use decimals here, but floats are good enough for now
            for row in buyrows:
                btw = row["prevalue"] * row["btw"] / 100
                buybtwtotals[row["btw"]] += btw
                row["btwvalue"] = btw

    for k, v in buybtwtotals.items():
        buybtwtotals[k] = int(round(v))

    for k, v in sellbtwtotals.items():
        sellbtwtotals[k] = int(round(v))

    return dict(sellbtwtotals), dict(buybtwtotals), sellrows, buyrows, servicerows


def transaction_record(transaction):
    sellbtwtotals, buybtwtotals, sellrows, buyrows, servicerows = transaction_process(transaction)

    total = sum([r['prevalue'] for r in sellrows]) - sum([r['prevalue'] for r in buyrows]) + sum(
        [r['prevalue'] for r in servicerows])

    if not transaction.two_to_one_has_btw:
        total -= sum(buybtwtotals.values())

    return {
        "reference": str(transaction.reference).zfill(4),
        "name": transaction.relation.get().name + " " + str(transaction.informal_reference).zfill(3),
        "sell": sellrows,
        "buy": buyrows,
        "service": servicerows,
        "sellbtw": sellbtwtotals,
        "buybtw": buybtwtotals,
        "description": transaction.description,
        "processeddate": transaction.processeddate,
        "deliverydate": transaction.deliverydate,
        "total": int(total),
        "id": transaction.key.urlsafe(),
        "revision": transaction.revision,
        "lastedit": transaction.lastedit,
        "two_to_one_has_btw": transaction.two_to_one_has_btw,
        "two_to_one_btw_per_row": transaction.two_to_one_btw_per_row
    }
