#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 08:48:01 2024

@author: jst072
"""
from src import rtp

def test_calc_nearest_range():
    assert rtp.calc_nearest_range(rtp.TimeInterval(0,1), 
                                  rtp.TimeInterval(1,2),1,10) == 5