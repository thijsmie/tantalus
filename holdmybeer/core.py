from .exceptions import RunDry, NegativeSubstance, IncompatibleContainer


class Bucket(object):
    """Holds an amount with a value that can be added to and substracted from."""
    
    def __init__(self, contenttype, amount, value):
        if amount < 0 or value < 0:
            raise NegativeSubstance()
        
        self.contenttype = contenttype   
        self.amount = amount
        self.value = value
        
        
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
        
        return Bucket(contenttype, amount, value)
        
    def give(self, contenttype, amount, value):
        if contenttype != self.contenttype:
            raise IncompatibleContainer()
            
        if amount < 0 or value < 0 or (amount == 0 and self.amount == 0 and value > 0):
            raise NegativeSubstance()
            
        self.amount += amount
        self.value += value
        
    def has(self, contenttype):
        return contenttype == self.contenttype
        
        
class Well(object):
    """Infinite source of pit that can be part of a transaction."""
    def __init__(self, contenttype, value):
        if value < 0:
            raise NegativeSubstance()
            
        self.contenttype = contenttype
        self.value = value
        
    def take(self, contenttype, amount):
        if contenttype != self.contenttype:
            raise IncompatibleContainer()
            
        return Bucket(contenttype, amount, amount*self.value)
        
    def give(self, contenttype, amount, value):
        if contenttype != self.contenttype:
            raise IncompatibleContainer()
    
    def has(self, contenttype):
        return contenttype == self.contenttype
