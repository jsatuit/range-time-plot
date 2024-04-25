#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 08:16:25 2024

"""
import numpy as np
from src.timeInterval import TimeInterval
from src.phaseshifter import PhaseShifter

def test_phaseshifter():
    ps = PhaseShifter()
    assert len(ps.phase_shifts) == 0
    
    # Create code
    code_len = 13
    code = np.random.randint(2, size = code_len)
    start = 10e-6
    baudlength = 1e-6
    
    for i, bit in enumerate(code):
        time = start + i * baudlength
        if bit == 0:
            ps.PHA0(time)
        else:
            ps.PHA180(time)
    
    # Test that phase_shifts are correct
    assert len(ps.phase_shifts) == code_len
    for i, phase in enumerate(ps.phase_shifts):
        assert phase.time == start + i * baudlength
        assert phase.event == code[i]*180
        
    # Test that phase_shift_within is correct
    ti1 = TimeInterval(start, start + code_len*baudlength)
    for i, phase_shift in enumerate(ps.phase_shifts_within(ti1)):
        assert phase_shift.time == ps.phase_shifts[i].time
        assert phase_shift.event == ps.phase_shifts[i].event
