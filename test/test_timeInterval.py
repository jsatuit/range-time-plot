# -*- coding: utf-8 -*-


import pytest

from src.timeInterval import TimeInterval, TimeIntervalList, OverlapError


def test_invalid_generation():
    with pytest.raises(ValueError):
        TimeInterval(1,0)
    with pytest.raises(TypeError):
        TimeInterval("qwert",6)
        
def rec_test_repr(ti):
    assert eval(repr(ti)) == ti
    
def test_empty_interval():
    ti = TimeInterval(0, 0)
    
    assert ti == ti*2
    assert ti == ti*20
    assert ti.length == 0.0
    assert ti.as_tuple == (0, 0)
    
def test_interval():
    tia = TimeInterval(1, 2)
    tib = TimeInterval(0, 4)
    tic = TimeInterval(2, 4)
    null = TimeInterval(0, 0)
    
    assert tia == tia
    assert tia*2 == tic
    assert tia*0 == null
    assert tic/2 == tia
    with pytest.raises(ZeroDivisionError):
        tia/0
    
    for ti in [tia, tib, tic, null]:
        rec_test_repr(ti)
        
    assert tia.length == 1
    assert tib.length == 4
    assert tic.length == 2
    
    assert tia.as_tuple == (1, 2)
    
    assert tia.overlaps_with(tib)
    assert not tia.overlaps_with(tic)
    assert not tia.overlaps_with(null)
    
    assert tib.overlaps_with(tia)
    assert tib.overlaps_with(tic)
    assert not tib.overlaps_with(null)
    
    assert not tic.overlaps_with(tia)
    assert tic.overlaps_with(tib)
    assert not tic.overlaps_with(null)
    
    with pytest.raises(OverlapError):
        tia.check_overlap(tib)
    tia.check_overlap(tic)
    tia.check_overlap(null)
    
    assert tia.within(tia)
    assert tia.within(tib)
    assert not tia.within(tic)
    assert not tic.within(tia)
    assert tic.within(tib)
    assert tic.within(tic)
    
# Test overlapping

def test_interval_list():
    tia = TimeInterval(1, 2)
    tib = TimeInterval(0, 4)
    tic = TimeInterval(2, 4)
    tl = TimeIntervalList((tia, tib, tic))
    assert tl[0] == tia
    assert tl[1] == tib
    assert tl[2] == tic
    assert tl.lengths == [1, 4, 2]
    assert tl.begins == [1, 0, 2]
    assert tl.ends == [2, 4, 4]