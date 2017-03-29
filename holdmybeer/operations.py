def flow(contenttype, source, destination, amount):
    splitoff = source.take(contenttype, amount)
    try:
        destination.give(contenttype, amount, splitoff.value)
    except:
        source.give(contenttype, amount, splitoff.value)
        raise
        
        

