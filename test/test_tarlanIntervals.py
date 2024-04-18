#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18 12:36:13 2024

@author: jsatuit
"""
import pytest  
from src.timeInterval import TimeInterval
from src.tarlanIntervals import IntervalList

def test_intervallist():
    # Test empty interval
    em = IntervalList("empty")
    assert em.name == "empty"
    assert not em.state
    assert em.is_off
    assert not em.is_on
    assert em.nstreams == 0
    assert len(em) == 0
    assert em.intervals == []
    with pytest.raises(RuntimeError):
        em.last_turn_off
    with pytest.raises(RuntimeError):
        em.last_turn_on
    
    # Test open interval
    op = IntervalList("open")
    op.turn_on(1, 1)
    assert op.name == "open"
    assert op.state
    assert not op.is_off
    assert op.is_on
    assert op.nstreams == 1
    assert len(op) == 1
    with pytest.raises(RuntimeError):
        op.intervals
    with pytest.raises(RuntimeError):
        op.last_turn_off
    assert op.last_turn_on == 1
    
    # Test closed interval
    cl = IntervalList("closed")
    cl.turn_on(1, 1)
    cl.turn_off(2,2)
    assert cl.name == "closed"
    assert not cl.state
    assert cl.is_off
    assert not cl.is_on
    assert cl.nstreams == 1
    assert len(cl) == 1
    assert cl.intervals == [TimeInterval(1, 2)]
    assert cl.last_turn_off == 2
    assert cl.last_turn_on == 1