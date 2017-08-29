from ndbextensions.validate import OperationError


def remove_mod_values(o):
    for i, m in enumerate(o.mods):
        mod = m.get()
        if mod.modifies:
            o.value -= o.modamounts[i]
    return o


def without_mod_values(o):
    value = o.value
    for i, m in enumerate(o.mods):
        mod = m.get()
        if mod.modifies:
            value -= o.modamounts[i]
    return value


def transform_collection(c1, c2, one_to_two):
    """Turn c1 into c2, as efficiently as possible. Might destroy c2 in the process."""

    c3 = []

    # First adapt shared items
    for r2 in c2[:]:
        for r1 in c1[:]:
            if r1.product == r2.product:
                adiff = r2.amount - r1.amount
                prd = r2.product.get()

                if one_to_two:
                    remove_mod_values(r1)
                    if adiff > 0:
                        tl = prd.take(adiff)
                        r2.value = r1.value + tl.value
                    elif adiff < 0:
                        tl = r1.take(-adiff)
                        r2.value = r1.value - tl.value
                        prd.give(tl)
                    else:
                        r2.value = r1.value
                    mods = r2.mods
                    r2.mods = []
                    r2.modamounts = []
                    for mod in mods:
                        mod.get().apply(r2)
                else:
                    vdiff = r2.value - r1.value
                    prd.value += vdiff
                    prd.amount += adiff

                prd.put()

                c3.append(r2)
                c1.remove(r1)
                c2.remove(r2)

                if prd.amount < 0 or prd.value < 0 or (prd.amount == 0 and prd.value != 0):
                    raise OperationError("Illegal state for {} would be created!".format(prd.name))
                break

    # Then, remove all items that have been removed
    for r1 in c1[:]:  # Make a slice so we can remove shit safely
        for r2 in c2:
            if r1.product == r2.product:
                break
        else:
            prd = r1.product.get()
            if one_to_two:
                prd.give(remove_mod_values(r1))
            else:
                prd.amount -= r1.amount
                prd.value -= r1.value
                if prd.amount < 0 or prd.value < 0 or (prd.amount == 0 and prd.value != 0):
                    raise OperationError("Illegal state for {} would be created!".format(prd.name))

            prd.put()
            c1.remove(r1)

    # Then, add all items that did not exist before
    for r2 in c2[:]:  # Make a slice so we can remove shit safely
        for r1 in c1:
            if r1.product == r2.product:
                break
        else:
            c2.remove(r2)
            prd = r2.product.get()
            if one_to_two:
                nr2 = prd.take(r2.amount)
                for mod in r2.mods:
                    mod.get().apply(nr2)
                r2 = nr2
            else:
                prd.give(r2)

            prd.put()
            c3.append(r2)

    return c3
