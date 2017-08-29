from holdmybeer.core import Bucket
from holdmybeer.exceptions import IncompatibleContainer, RunDry
from holdmybeer.util import divide


class Bucketlist(object):
    """Collection of buckets that can be accessed in one go."""
    singletype = Bucket
    makemydict = True
    autocreate = False

    def __init__(self, autocreate=None):
        if self.makemydict:
            self.mydict = {}
            self.autocreate = autocreate or self.autocreate

    def append(self, bucket):
        if type(bucket) is not self.singletype:
            raise IncompatibleContainer()
        if bucket.contenttype in self.mydict:
            self.mydict[bucket.contenttype].absorb(bucket)
            return self.mydict[bucket.contenttype]
        self.mydict[bucket.contenttype] = bucket
        return bucket

    def take(self, contenttype, amount):
        if contenttype in self.mydict:
            return self.mydict[contenttype].take(contenttype, amount)
        raise IncompatibleContainer()

    def give(self, contenttype, amount, value):
        if contenttype in self.mydict:
            self.mydict[contenttype].give(contenttype, amount, value)
            return
        if self.autocreate:
            self.append(self.singletype(contenttype, amount, value))
        else:
            raise IncompatibleContainer()

    def dump(self):
        return [b.dump() for b in self.mydict.values()]

    def absorb(self, other):
        dump = other.dump()
        try:
            for b in dump:
                self.give(b.contenttype, b.amount, b.value)
        except:
            for b in dump:
                other.absorb(b)
            raise
        return dump

    def clone(self):
        ls = self.__class__(self.autocreate)
        for c, b in self.mydict.iteritems():
            ls.mydict[c] = b.clone()
        return ls

    def has(self, contenttype):
        if contenttype in self.mydict:
            return True
        return False

    def get_bucket(self, contenttype):
        if self.has(contenttype):
            return self.mydict[contenttype]
        raise RunDry()


class RatioBucket(object):
    """Has a collection of items that are given out in certain ratio."""
    listtype = Bucketlist
    singletype = Bucket

    def __init__(self, contenttype, ratios):
        """param ratios: dict(contenttype: ratio)"""
        self.contenttype = contenttype
        self.mylist = self.listtype(autocreate=True)
        self.ratios = ratios

    def take(self, contenttype, amount):
        if contenttype == self.contenttype:
            value = 0
            for ctype, ratio in self.ratios.items():
                value += self.mylist.take(ctype, int(round(amount * ratio))).value
            return self.singletype(self.contenttype, amount, value)
        else:
            return self.mylist.take(contenttype, amount)

    def give(self, contenttype, amount, value):
        if contenttype == self.contenttype:
            # We must be careful here
            # we should divvy up the value into integers but the total should be equal, see util
            ctypes = self.ratios.keys()
            ratios = [self.ratios[ctype] for ctype in ctypes]
            values = divide(amount, ratios)

            for i in range(len(values)):
                self.mylist.give(ctypes[i], int(round(amount * ratios[i])), values[i])
        else:
            self.mylist.give(contenttype, amount, value)

    def dump(self):
        return self.mylist.dump()

    def absorb(self, other):
        self.mylist.absorb(other)

    def has(self, contenttype):
        if contenttype == self.contenttype:
            return True
        return self.mylist.has(contenttype)


class Bucketcrate(Bucket):
    """Bucket of items that can be in packed together into a 'crate'.
     For example a trays of beer: they can either be counted in bottles or trays."""

    def __init__(self, single_contenttype, crate_contenttype, per_crate, amount, value):
        super(self.__class__, self).__init__(single_contenttype, amount, value)
        self.crate_contenttype = crate_contenttype
        self.per_crate = per_crate

    def take(self, contenttype, amount):
        if contenttype == self.crate_contenttype:
            return super(self.__class__, self).take(self.contenttype, amount * self.per_crate)
        else:
            return super(self.__class__, self).take(contenttype, amount)

    def give(self, contenttype, amount, value):
        if contenttype == self.crate_contenttype:
            return super(self.__class__, self).give(self.contenttype, amount * self.per_crate, value)
        else:
            return super(self.__class__, self).give(contenttype, amount, value)

    def dump(self):
        return super(self.__class__, self).dump()

    def absorb(self, other):
        super(self.__class__, self).absorb(other)

    def clone(self):
        return self.__class__(self.contenttype, self.crate_contenttype, self.per_crate, self.amount, self.value)

    def has(self, contenttype):
        return contenttype == self.contenttype or contenttype == self.crate_contenttype


class Stream:
    listtype = Bucketlist

    def __init__(self):
        self.one_to_two = self.listtype(autocreate=True)
        self.two_to_one = self.listtype(autocreate=True)

    def send_one_to_two(self, bucket):
        return self.one_to_two.append(bucket.clone())

    def send_two_to_one(self, bucket):
        return self.two_to_one.append(bucket.clone())
