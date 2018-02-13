from google.appengine.ext.ndb import Key, transactional
from ndbextensions.models import Transaction, TransactionLine, ServiceLine, TypeGroup
from ndbextensions.validate import OperationError

from api.actions.rows import transform_collection

from datetime import datetime
from pytz import timezone


def new_transaction(data,):
    relation = Key('Relation', int(data["relation"]), parent=TypeGroup.relation_ancestor())
    if relation.get() is None:
        raise OperationError("Relation does not exist!")

    tr = Transaction.query(Transaction.relation == relation).order(-Transaction.reference).get()
    if tr is None:
        reference = 1
    else:
        reference = tr.reference + 1

    t = Transaction(
        revision=0,
        reference=reference,
        relation=relation,
        deliverydate=datetime.strptime(data["deliverydate"], "%Y-%m-%d").date(),
        processeddate=datetime.now(timezone("Europe/Amsterdam")).date(),
        description=data.get("description", "")
    )

    @transactional(xg=True)
    def tricky_stuff():
        for prd in data["sell"]:
            product = Key('Product', int(prd['id']), parent=TypeGroup.product_ancestor()).get()
            if product is None:
                raise OperationError("Product with id {} does not exist.".format(product))
            line = product.take(int(prd['amount']))
            product.put()

            for mod in prd["mods"]:
                mod_obj = Key('Mod', int(mod), parent=TypeGroup.product_ancestor()).get()
                if mod_obj is None:
                    raise OperationError("Mod with id {} does not exist.".format(mod))
                mod_obj.apply(line)

            t.one_to_two.append(line)

        for prd in data["buy"]:
            product = Key('Product', int(prd['id']), parent=TypeGroup.product_ancestor()).get()
            if product is None:
                raise OperationError("Product with id {} does not exist.".format(product))
            line = TransactionLine(
                product=product.key,
                amount=int(prd['amount']),
                value=int(prd['price'])
            )

            for mod in prd["mods"]:
                mod_obj = Key('Mod', int(mod), parent=TypeGroup.product_ancestor()).get()
                if mod_obj is None:
                    raise OperationError("Mod with id {} does not exist.".format(mod))
                mod_obj.apply(line)

            product.give(line)
            product.put()
            t.two_to_one.append(line)

    tricky_stuff()
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
        product = Key('Product', int(prd['id']), parent=TypeGroup.product_ancestor()).get()
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(product))

        line = TransactionLine(
            value=0,
            amount=int(prd['amount']),
            product=product.key
        )
        product.put()

        for mod in prd["mods"]:
            mod_obj = Key('Mod', int(mod), parent=TypeGroup.product_ancestor()).get()
            if mod_obj is None:
                raise OperationError("Mod with id {} does not exist.".format(mod))
            line.mods.append(mod_obj.key)

        newsell.append(line)

    t.one_to_two = transform_collection(t.one_to_two, newsell, True)

    newbuy = []
    for prd in data["buy"]:
        product = Key('Product', int(prd['id']), parent=TypeGroup.product_ancestor()).get()
        if product is None:
            raise OperationError("Product with id {} does not exist.".format(product))
        line = TransactionLine(
            product=product.key,
            amount=int(prd['amount']),
            value=int(prd['price'])
        )

        for mod in prd["mods"]:
            mod_obj = Key('Mod', int(mod), parent=TypeGroup.product_ancestor()).get()
            if mod_obj is None:
                raise OperationError("Mod with id {} does not exist.".format(mod))
            mod_obj.apply(line)

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

    t.total = transaction_total(t)
    t.put()
    return t


def get_mod_collection(collection):
    mods = set()
    for row in collection:
        for mod in row.mods:
            mods.add(mod)
    return list(mods)


def get_mod_totals(collection):
    mods = get_mod_collection(collection)
    totals = []
    for row in collection:
        rowtotals = [0] * len(mods)
        for i, mod in enumerate(row.mods):
            rowtotals[mods.index(mod)] = row.modamounts[i]
        totals.append(rowtotals)
    return mods, totals


def make_row_record(row, mods, modtotals):
    prevalue = row.value
    total = row.value

    for i, mod in enumerate(mods):
        if mod.get().modifies:
            prevalue -= modtotals[i]
        else:
            total += modtotals[i]

    return {
        "contenttype": row.product.get().contenttype,
        "value": row.value,
        "prevalue": prevalue,
        "modtotals": modtotals,
        "amount": row.amount,
        "unit": int(round(total / row.amount)),
        "total": total
    }
    
    
def get_row_prepost(row):
    prevalue = row.value
    total = row.value

    for i, mod in enumerate(row.mods):
        if mod.get().modifies:
            prevalue -= row.modamounts[i]
        else:
            total += row.modamounts[i]

    return prevalue, total


def transaction_record(transaction):
    smods, stotals = get_mod_totals(transaction.one_to_two)
    bmods, btotals = get_mod_totals(transaction.two_to_one)
    sellrows = [make_row_record(row, smods, stotals[i]) for i, row in enumerate(transaction.one_to_two)]
    buyrows = [make_row_record(row, bmods, btotals[i]) for i, row in enumerate(transaction.two_to_one)]
    servicerows = [{"contenttype": row.service, "amount": row.amount, "value": row.value} for row in
                   transaction.services]

    total = sum([r['total'] for r in sellrows]) - sum([r['total'] for r in buyrows]) + sum(
        [r['value'] for r in servicerows])
    sell = {
        "modnames": [mod.get().name for mod in smods],
        "rows": sellrows
    }
    buy = {
        "modnames": [mod.get().name for mod in bmods],
        "rows": buyrows
    }
    service = {
        "rows": servicerows
    }
    return {
        "name": transaction.relation.get().name + " " + str(transaction.reference).zfill(3),
        "sell": sell,
        "buy": buy,
        "service": service,
        "description": transaction.description,
        "processeddate": transaction.processeddate,
        "deliverydate": transaction.deliverydate,
        "total": total,
        "id": transaction.key.id(),
        "revision": transaction.revision,
        "lastedit": transaction.lastedit
    }


def transaction_total(transaction):
    smods, stotals = get_mod_totals(transaction.one_to_two)
    bmods, btotals = get_mod_totals(transaction.two_to_one)
    sellrows = [make_row_record(row, smods, stotals[i]) for i, row in enumerate(transaction.one_to_two)]
    buyrows = [make_row_record(row, bmods, btotals[i]) for i, row in enumerate(transaction.two_to_one)]
    return sum([r['total'] for r in sellrows]) - sum([r['total'] for r in buyrows]) + sum(
        [r.value for r in transaction.services])


def tool_reapply_transaction_adding(transaction):
    # This method will reapply a transaction to stock
    # tool for testing

    for row in transaction.two_to_one:
        product = row.product.get()
        product.amount += row.amount
        product.value += row.value
        product.put()


def tool_reapply_transaction_removing(transaction):
    for row in transaction.one_to_two:
        product = row.product.get()
        prevalue = row.value
        for i, mod in enumerate(row.mods):
            if mod.get().modifies:
                prevalue -= row.modamounts[i]
        product.amount -= row.amount
        product.value -= prevalue
        product.put()

