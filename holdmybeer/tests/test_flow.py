import pytest

from holdmybeer import Bucket, Well, IncompatibleContainer, NegativeSubstance, flow


def test_well_to_well():
    wella = Well('a', 10)
    wellb = Well('a', 10)
    wellc = Well('b', 10)
    
    with pytest.raises(IncompatibleContainer):
        flow('b', wella, wellb, 10)
        
    with pytest.raises(NegativeSubstance):
        flow('a', wella, wellb, -10)
        
    with pytest.raises(IncompatibleContainer):
        flow('a', wella, wellc, 10)
        
    flow('a', wella, wellb, 10)
        
def test_well_to_bucket():
    wella = Well('a', 10)
    
    bucketa = Bucket('a', 10, 200)
    bucketb = Bucket('b', 17, 100)
    
    with pytest.raises(IncompatibleContainer):
        flow('a', wella, bucketb, 10)
        
    assert bucketb.amount == 17
    assert bucketb.value == 100
    
    with pytest.raises(IncompatibleContainer):
        flow('b', wella, bucketb, 10)
        
    assert bucketb.amount == 17
    assert bucketb.value == 100
    
    flow('a', wella, bucketa, 10)
    
    assert bucketa.amount == 20
    assert bucketa.value == 300
    
def test_bucket_to_well():
    bucketa = Bucket('a', 10, 200)
    bucketb = Bucket('b', 17, 100)
    
    wella = Well('a', 10)
    
    with pytest.raises(IncompatibleContainer):
        flow('b', bucketb, wella, 10)
        
    assert bucketb.amount == 17
    assert bucketb.value == 100    
        
    with pytest.raises(IncompatibleContainer):
        flow('b', bucketb, wella, 10)
    
    assert bucketa.amount == 10
    assert bucketa.value == 200
    
    flow('a', bucketa, wella, 7)
    
    assert bucketa.amount == 3
    assert bucketa.value == 60
    
def test_bucket_to_bucket():
    bucketa = Bucket('a', 10, 200)
    bucketb = Bucket('b', 17, 100)
    bucketc = Bucket('a', 10, 105)
    
    with pytest.raises(IncompatibleContainer):
        flow('b', bucketa, bucketb, 10)
        
    assert bucketa.amount == 10
    assert bucketa.value == 200
    assert bucketb.amount == 17
    assert bucketb.value == 100    
        
    with pytest.raises(IncompatibleContainer):
        flow('a', bucketa, bucketb, 10)    
        
    assert bucketa.amount == 10
    assert bucketa.value == 200
    assert bucketb.amount == 17
    assert bucketb.value == 100
    
    flow('a', bucketc, bucketc, 7)
    
    assert bucketc.amount == 10
    assert bucketc.value == 105
    
    flow('a', bucketc, bucketa, 7)
    
    assert bucketc.amount == 3
    assert bucketc.value == 31
    assert bucketa.amount == 17
    assert bucketa.value == 274
