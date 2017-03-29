"""
How to divide an amount according to ratios, without introducing rounding errors? A clean implementation is the
largest remainder method, see https://en.wikipedia.org/wiki/Largest_remainder_method or
http://stackoverflow.com/questions/13483430/how-to-make-rounded-percentages-add-up-to-100
"""

def divide(amount, ratios):
    total = sum(ratios)
    truediv = [amount * r / float(total) for r in ratios]
    floordiv = [int(div) for div in truediv]
    
    diff = amount - sum(floordiv)
    # We can only be to low, since we round down. Increase those with largest fractions.
    order = argsort_by_fraction(truediv)
    for i in range(diff):
        floordiv[order[i]] += 1
        
    return floordiv   
    

def argsort_by_fraction(array):
    fractions = [1-(num % 1.0) for num in array]
    # see http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python
    return sorted(range(len(fractions)), key=fractions.__getitem__)
    
