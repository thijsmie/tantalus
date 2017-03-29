class RunDry(Exception):
    """Attempted to get more out of a bucket than it contains."""
    
    
class NegativeSubstance(Exception):
    """Attempted to initialize or modify a bucket with negative values"""


class IncompatibleContainer(Exception):
    """Attempted to flow to an incompatable container"""
