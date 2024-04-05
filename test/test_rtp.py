#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 08:48:01 2024

@author: jst072
"""
from src import rtp
import pytest

def test_calc_nearest_range():
    assert rtp.calc_nearest_range(rtp.TimeInterval(0,1), 
                                  rtp.TimeInterval(1,2),1,10) == 5
    # Test varying baud length
    assert rtp.calc_nearest_range(rtp.TimeInterval(0,1), 
                                  rtp.TimeInterval(1,2),0.1,10) == 0.5
    
    # Test varying starttime for reception
    assert rtp.calc_nearest_range(rtp.TimeInterval(0,1), 
                                  rtp.TimeInterval(10,12),1,10) == 50
    
    # Test varying endtime for reception
    assert rtp.calc_nearest_range(rtp.TimeInterval(0,1), 
                                  rtp.TimeInterval(1,20),1,10) == 5
    
    # Test displacement in time
    assert rtp.calc_nearest_range(rtp.TimeInterval(10,11), 
                                  rtp.TimeInterval(11,12),1,10) == 5
    
    # Test varying travel velocity
    assert rtp.calc_nearest_range(rtp.TimeInterval(0,1), 
                                  rtp.TimeInterval(1,2),1,100) == 50
    
    # Test Overlapping intervals
    with pytest.raises(rtp.OverlapError):
        rtp.calc_nearest_range(rtp.TimeInterval(0,1), 
                               rtp.TimeInterval(0,1),1)
    with pytest.raises(rtp.OverlapError):
        rtp.calc_nearest_range(rtp.TimeInterval(0,1), 
                                  rtp.TimeInterval(0,1),0.1)
    
    