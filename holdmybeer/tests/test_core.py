import pytest

from holdmybeer import Bucket, Well, NegativeSubstance, RunDry, IncompatibleContainer


def test_bucket_init():
    bk = Bucket('beer', 2, 3)
    assert bk.contenttype == 'beer'
    assert bk.amount == 2
    assert bk.value == 3

    with pytest.raises(NegativeSubstance):
        Bucket('b', -1, 0)
    with pytest.raises(NegativeSubstance):
        Bucket('b', 10, -2)


def test_well_init():
    wl = Well('beer', 10)
    assert wl.contenttype == 'beer'
    assert wl.value == 10

    with pytest.raises(NegativeSubstance):
        Well('b', -1)


def test_bucket_take():
    bucket = Bucket('beer', 2, 5)

    with pytest.raises(IncompatibleContainer):
        bucket.take('eeeh', 1)

    with pytest.raises(RunDry):
        bucket.take('beer', 3)

    with pytest.raises(NegativeSubstance):
        bucket.take('beer', 0)

    newbucket = bucket.take('beer', 1)

    assert bucket.amount == 1
    assert newbucket.contenttype == 'beer'
    assert newbucket.amount == 1
    assert newbucket.value + bucket.value == 5


def test_bucket_give():
    bucket = Bucket('beer', 2, 3)

    with pytest.raises(IncompatibleContainer):
        bucket.give('eeeh', 1, 1)

    with pytest.raises(NegativeSubstance):
        bucket.give('beer', -1, 1)

    bucket.give('beer', 1, 1)

    assert bucket.amount == 3
    assert bucket.value == 4


def test_well_take():
    well = Well('beer', 2)

    with pytest.raises(IncompatibleContainer):
        well.take('eeeh', 10)

    bucket = well.take('beer', 10)

    assert well.value == 2
    assert bucket.contenttype == 'beer'
    assert bucket.amount == 10
    assert bucket.value == 20


def test_well_give():
    well = Well('beer', 2)

    with pytest.raises(IncompatibleContainer):
        well.give('eeeh', 10, 10)

    well.give('beer', 10, 10)

    assert well.contenttype == 'beer'
    assert well.value == 2


def test_bucket_well_has():
    well = Well('beer', 1)
    bucket = Bucket('beer', 1, 1)

    assert well.has('beer')
    assert not well.has('notbeer')
    assert bucket.has('beer')
    assert not bucket.has('notbeer')
