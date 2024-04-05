# -*- coding: utf-8 -*-


import pytest

from src.timeInterval import TimeInterval, OverlapError


def test_invalid_generation():
    with pytest.raises(ValueError):
        TimeInterval(1,0)
    with pytest.raises(TypeError):
        TimeInterval("wert",6)
        
def test_repr(ti):
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
    
    for ti in [tia, tib, tic, null]:
        test_repr(ti)
        
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
    
    
    with pytest.raises(TypeError):
        tia/3

# Test «normal» interval

# Test overlapping