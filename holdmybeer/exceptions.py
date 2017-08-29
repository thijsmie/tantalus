class RunDry(Exception):
    """Attempted to get more out of a bucket than it contains."""

    def __init__(self, product=None, amount=0):
        self.product = product
        self.amount = amount


class NegativeSubstance(Exception):
    """Attempted to initialize or modify a bucket with negative values"""

    def __init__(self, product=None):
        self.product = product


class IncompatibleContainer(Exception):
    """Attempted to flow to an incompatable container"""

    def __init__(self, product=None, other=None):
        self.product = product
        self.other = other
