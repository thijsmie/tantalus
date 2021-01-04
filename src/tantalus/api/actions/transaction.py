from tantalus_db.base import db
from tantalus_db.models import Referencing, Transaction, TransactionLine, ServiceLine, Relation, Product, BtwType
from tantalus_db.validate import OperationError
from tantalus_db.utility import get_or_none, transactional

from api.actions.rows import transform_collection

from collections import defaultdict
from datetime import datetime
from pytz import timezone


@transactional
def new_transaction(data):
    relation = get_or_none(data['relation'], Relation)
    
    if relation is None:
        raise OperationError("Relation does not exist!")
    
    if relation.numbered_reference:
        reference = Referencing.get_reference()
    else:
        reference = 0        

    tr = Transaction.query.filter(Transaction.relation == relation.key).order_by(
        Transaction.informal_reference.desc()).first_or_none()

    if tr is None:
        informal_reference = 1
    else:
        informal_reference = tr.informal_reference + 1

    t = Transaction(
        reference=reference,
        informal_reference=informal_reference,
        relation=relation,
        deliverydate=datetime.strptime(data["deliverydate"], "%Y-%m-%d").date(),
        processeddate=datetime.now(timezone("Europe/Amsterdam")).date(),
        description=data.get("description", ""),
        two_to_one_has_btw=data.get("two_to_one_has_btw", False),
        two_to_one_btw_per_row=data.get("two_to_one_btw_per_row", False)
    )

    for prd in data["sell"]:
        product = get_or_none(prd["id"], Product)
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))
        line = product.take(int(prd['amount']))
        t.one_to_two.append(line)

    for prd in data["buy"]:
        product = get_or_none(prd["id"], Product)
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(prd["id"]))

        line = TransactionLine(
            product=product,
            amount=int(prd['amount']),
            prevalue=int(prd['price']),
            value=product.value * int(prd['amount']),
            btwtype=product.btwtype
        )

        product.give(line)
        t.two_to_one.append(line)

    for prd in data["service"]:
        btw = prd.get('btw', 0)
        btwtype = BtwType.query.filter(BtwType.percentage == btw).first_or_none()

        if btwtype is None:
            btwtype = BtwType(
                name=str(btw)+"%",
                percentage=btw
            )
            db.session.add(btwtype)
    
        line = ServiceLine(
            service=prd['contenttype'],
            amount=int(prd['amount']),
            value=int(prd['price']),
            btwtype=btwtype
        )

        t.services.append(line)

    rec = transaction_record(t)
    t.total = rec["total"]
    db.session.add(t)

    return t


@transactional
def edit_transaction(t, data):
    # Easy stuff first
    # Note, this does not take care of money in budgets, do outside! Something with transactional limitations...
    t.revision += 1
    
    t.two_to_one_has_btw = data.get("two_to_one_has_btw", t.two_to_one_has_btw)
    t.two_to_one_btw_per_row = data.get("two_to_one_btw_per_row", t.two_to_one_btw_per_row)

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
            product=product,
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
            product=product,
            amount=int(prd['amount']),
            prevalue=int(prd['price']),
            value=int(prd['amount'])*product.value,
            btwtype=product.btwtype
        )

        newbuy.append(line)
    t.two_to_one = transform_collection(t.two_to_one, newbuy, False)

    t.services = []
    for prd in data["service"]:
        btw = prd.get('btw', 0)
        btwtype = BtwType.query.filter(BtwType.percentage == btw).first_or_none()
        if btwtype is None:
            btwtype = BtwType(
                name=str(btw)+"%",
                percentage=btw
            )
            db.session.add(btwtype)
    
        line = ServiceLine(
            service=prd['contenttype'],
            amount=int(prd['amount']),
            value=int(prd['price']),
            btwtype=btwtype.key
        )

        t.services.append(line)

    record = transaction_record(t)
    t.total = record["total"]
    db.session.add(t)
    return t


def make_row_record(row):
    return {
        "contenttype": row.product.contenttype,
        "group": row.product.group.name,
        "prevalue": row.prevalue,
        "value": row.value,
        "amount": row.amount,
        "btw": row.btwtype.percentage
    }


def make_service_record(row):
    return {
        "contenttype": row.service,
        "amount": row.amount,
        "prevalue": row.value,
        "value": row.value,
        "btw": row.btwtype.percentage
    }


def transaction_process(transaction):
    sellrows = [make_row_record(row) for row in transaction.one_to_two]
    buyrows = [make_row_record(row) for row in transaction.two_to_one]
    servicerows = [make_service_record(row) for row in transaction.services]

    btwtotals = defaultdict(float)
    btwvalues = defaultdict(int)
    # Current total including btw, btw rounded per invoice
    for row in sellrows:
        btw = row["prevalue"] * row["btw"] / 100. / (row["btw"]/100. + 1)
        btwtotals[row["btw"]] -= btw
        btwvalues[row["btw"]] -= row["prevalue"]
        row["btwvalue"] = btw

    # Current total including btw, btw rounded per invoice
    for row in servicerows:
        btw = row["prevalue"] * row["btw"] / 100. / (row["btw"]/100. + 1)
        btwtotals[row["btw"]] -= btw
        btwvalues[row["btw"]] -= row["prevalue"]
        row["btwvalue"] = btw

    buybtwtotals = defaultdict(float)
    for row in buyrows:
        if transaction.two_to_one_has_btw:
            if transaction.two_to_one_btw_per_row:
                # Current total including btw, btw rounded per row
                btw = round(row["prevalue"] * row["btw"] / 100.0 / (row["btw"]/100. + 1))
            else:
                # Current total including btw, btw rounded for full invoice
                # We should use decimals here, but floats are good enough for now
                btw = row["prevalue"] * row["btw"] / 100. / (row["btw"]/100. + 1)
        else:
            if transaction.two_to_one_btw_per_row:
                # Current total excluding btw, btw rounded per row
                btw = round(row["prevalue"] * row["btw"] / 100.0)
                btwvalues[row["btw"]] += btw
            else:
                # Current total excluding btw, btw rounded for full invoice
                # We should use decimals here, but floats are good enough for now
                btw = row["prevalue"] * row["btw"] / 100.0
                btwvalues[row["btw"]] += btw
        btwvalues[row["btw"]] += row["prevalue"]
        btwtotals[row["btw"]] += btw
        buybtwtotals[row["btw"]] += btw
        row["btwvalue"] = btw
        row["value_exl"] = row["value"] * (1 - row["btw"] / 100.0 / (row["btw"]/100. + 1))

    for k, v in btwtotals.items():
        btwtotals[k] = int(round(v))
        
    return dict(btwtotals), dict(btwvalues), dict(buybtwtotals), sellrows, buyrows, servicerows


def transaction_record(transaction):
    btwtotals, btwvalues, buybtwtotals, sellrows, buyrows, servicerows = transaction_process(transaction)

    selltotal = sum(r['prevalue'] for r in sellrows)
    buytotal = sum(r['prevalue'] for r in buyrows)
    servicetotal = sum(r['prevalue'] for r in servicerows)
    
    total = selltotal - buytotal + servicetotal
    
    if not transaction.two_to_one_has_btw:   
        total -= sum(buybtwtotals.values())

    return {
        "reference": str(transaction.reference).zfill(4),
        "name": transaction.relation.name + " " + str(transaction.informal_reference).zfill(3),
        "sell": sellrows,
        "buy": buyrows,
        "service": servicerows,
        "selltotal": selltotal,
        "buytotal": buytotal,
        "btwtotals": btwtotals,
        "btwvalues": btwvalues,
        "btwtotal": sum(btwtotals.values()),
        "servicetotal": servicetotal,
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

