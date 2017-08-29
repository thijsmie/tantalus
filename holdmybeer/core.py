from holdmybeer.exceptions import RunDry, NegativeSubstance, IncompatibleContainer


class Bucket(object):
    """Holds an amount with a value that can be added to and substracted from."""

    def __init__(self, contenttype, amount, value):
        if amount < 0 or value < 0:
            raise NegativeSubstance()

        self.contenttype = contenttype
        self.amount = amount
        self.value = value
        self.prevalue = value
        self.mods = []

    def take(self, contenttype, amount):
        if contenttype != self.contenttype:
            raise IncompatibleContainer()

        if amount <= 0:
            raise NegativeSubstance()

        if amount > self.amount:
            raise RunDry()

        value = round(self.value * amount / self.amount)
        self.amount -= amount
        self.value -= value

        return self.__class__(contenttype, amount, value)

    def give(self, contenttype, amount, value):
        if contenttype != self.contenttype:
            raise IncompatibleContainer()

        if amount < 0 or value < 0 or (amount == 0 and self.amount == 0 and value > 0):
            raise NegativeSubstance()

        self.amount += amount
        self.value += value

    def dump(self):
        ret = [self.__class__(contenttype=self.contenttype, amount=self.amount, value=self.value)]
        self.amount = 0
        self.value = 0
        return ret

    def clone(self):
        return self.__class__(contenttype=self.contenttype, amount=self.amount, value=self.value)

    def absorb(self, other):
        todo = other.dump()
        try:
            for b in todo:
                self.give(b.contenttype, b.amount, b.value)
        except:
            for b in todo:
                other.absorb(b)
            raise

        other.amount = 0
        other.value = 0

    def has(self, contenttype):
        return contenttype == self.contenttype


class Well(object):
    """Infinite source of pit that can be part of a transaction."""
    singletype = Bucket

    def __init__(self, contenttype, value):
        if value < 0:
            raise NegativeSubstance()

        self.contenttype = contenttype
        self.value = value
        self.amount = 0

    def take(self, contenttype, amount):
        if contenttype != self.contenttype:
            raise IncompatibleContainer()

        return self.singletype(contenttype, amount, amount * self.value)

    def give(self, contenttype, amount, value):
        if contenttype != self.contenttype:
            raise IncompatibleContainer()

    def dump(self):
        return [self]

    def clone(self):
        return self.__class__(self.contenttype, self.value)

    def absorb(self, other):
        self.give(other.contenttype, other.amount, other.value)

        other.amount = 0
        other.value = 0

    def has(self, contenttype):
        return contenttype == self.contenttype
