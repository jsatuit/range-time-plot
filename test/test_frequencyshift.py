#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 12:38:30 2024

"""
import pytest

from src.timeInterval import TimeInterval
from src.frequencyshift import FrequencyList

def test_as_line():
    f = {
        1: 100,
        2: 135,
        5: 274,
        23: 34,
    }
    fl = FrequencyList(f)
    
    assert fl.as_line(TimeInterval(1, 5)) == ([1, 2, 2, 5], [100, 100, 135, 135])
    assert fl.as_line((1, 2)) == ([1, 2], [100, 100])
    assert fl.as_line(24) == ([1, 2, 2, 5, 5, 23, 23, 24], [100, 100, 135, 135, 274, 274, 34, 34])
    with pytest.raises(TypeError):
        fl.as_line()
    with pytest.raises(ValueError):
        fl.as_line((0,2))
    with pytest.raises(ValueError):
        fl.as_line(0)