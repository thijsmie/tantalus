
def transform_collection(c1, c2, one_to_two):
    """Turn c1 into c2, as efficiently as possible. Will destroy c1/c2 in the process."""

    c3 = []

    # Adapt shared items. Equal types are forced. Cannot edit lines that have a different
    # Standard value than the current.
    for r1 in c1[:]:
        for r2 in c2[:]:
            prd = r1.product.get()
            if r1.product == r2.product and r1.value / r1.amount == prd.value:
                # This matches, remove them from the "To process" stacks
                c1.remove(r1)
                c2.remove(r2)
                c3.append(r2)
                if r1.amount == r2.amount:
                    # No change, remove and continue
                    break
                more = r2.amount > r1.amount
                if one_to_two and more:
                    # Selling more
                    prd.take(r2.amount - r1.amount)
                elif one_to_two and not more:
                    # Selling less
                    # We know it sold for the unit price, so just give that back
                    prd.give(r1.amount - r2.amount)
                elif not one_to_two and more:
                    # Buying more
                    prd.give(r2.amount - r1.amount)
                elif not one_to_two and not more:
                    # Buying less
                    prd.take(r1.amount - r2.amount)
                prd.put()
                break

    # Undo everything no longer in the transaction
    for r1 in c1:
        prd = r1.product.get()
        if one_to_two:
            # We sold r1.amount but we dont want to anymore, give it back
            prd.give(r1.amount)
        else:
            # We bought r1.amount but we dont want to anymore, give it back
            prd.take(r1.amount)
        prd.put()

    # Add everything new in the transaction
    for r2 in c2:
        prd = r2.product.get()
        if one_to_two:
            # We want to sell r2.amount
            prd.take(r2.amount)
        else:
            # We want to buy r2.amount
            prd.give(r2.amount)
        c3.append(r2)
        prd.put()

    return c3
