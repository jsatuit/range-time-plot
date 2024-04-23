#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 08:48:01 2024

@author: jsatuit
"""
from src.expplot import calc_nearest_range, calc_furthest_full_range#, Expplot
import src.timeInterval as ti
import pytest

def test_calc_nearest_range():
    assert calc_nearest_range(ti.TimeInterval(0,1), 
                                  ti.TimeInterval(1,2),1,10) == 5
    # Test varying baud length
    assert calc_nearest_range(ti.TimeInterval(0,1), 
                                  ti.TimeInterval(1,2),0.1,10) == 0.5
    
    # Test varying starttime for reception
    assert calc_nearest_range(ti.TimeInterval(0,1), 
                                  ti.TimeInterval(10,12),1,10) == 50
    
    # Test varying endtime for reception
    assert calc_nearest_range(ti.TimeInterval(0,1), 
                                  ti.TimeInterval(1,20),1,10) == 5
    
    # Test displacement in time
    assert calc_nearest_range(ti.TimeInterval(10,11), 
                                  ti.TimeInterval(11,12),1,10) == 5
    
    # Test varying travel velocity
    assert calc_nearest_range(ti.TimeInterval(0,1), 
                                  ti.TimeInterval(1,2),1,100) == 50
    
    # Test Overlapping intervals
    with pytest.raises(ti.OverlapError):
        calc_nearest_range(ti.TimeInterval(0,1), 
                               ti.TimeInterval(0,1),1)
    with pytest.raises(ti.OverlapError):
        calc_nearest_range(ti.TimeInterval(0,1), 
                               ti.TimeInterval(0,1),0.1)
    
def test_calc_furthest_full_range():
    assert calc_furthest_full_range(ti.TimeInterval(0,1), 
                                        ti.TimeInterval(1,2),1,10) == 5
    # Test varying baud length
    assert calc_furthest_full_range(ti.TimeInterval(0,1), 
                                        ti.TimeInterval(1,2),0.1,10) == 5
    
    # Test varying starttime for reception
    assert calc_furthest_full_range(ti.TimeInterval(0,1), 
                                        ti.TimeInterval(10,12),1,10) == 55
    
    # Test varying endtime for reception
    assert calc_furthest_full_range(ti.TimeInterval(0,1), 
                                        ti.TimeInterval(1,20),1,10) == 95
    
    # Test displacement in time
    assert calc_furthest_full_range(ti.TimeInterval(10,11), 
                                        ti.TimeInterval(11,12),1,10) == 5
    
    # Test varying travel velocity
    assert calc_furthest_full_range(ti.TimeInterval(0,1), 
                                        ti.TimeInterval(1,2),1,100) == 50
    
    # Test Overlapping intervals
    with pytest.raises(ti.OverlapError):
        calc_furthest_full_range(ti.TimeInterval(0,1), ti.TimeInterval(0,1),1)
    with pytest.raises(ti.OverlapError):
        calc_furthest_full_range(ti.TimeInterval(0,1), ti.TimeInterval(0,1),0.1)