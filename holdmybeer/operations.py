from math import floor, ceil


def flow(contenttype, source, destination, amount):
    splitoff = source.take(contenttype, amount)
    try:
        destination.give(contenttype, amount, splitoff.value)
    except:
        source.give(contenttype, amount, splitoff.value)
        raise


class FlowMod:
    def __init__(self, pre_add, multiplier, post_add, included=False, rounding=None, divides=False):
        self.pre_add = pre_add
        self.multiplier = multiplier
        self.post_add = post_add
        self.modifies = included
        self.rounding = rounding
        self.divides = divides
        self.key = ""
