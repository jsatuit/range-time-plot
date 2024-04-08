#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.tarlan import Tarlan, TarlanError

import pytest

def test_tarlan_parsing():
    tlan = Tarlan()
    
    # Check that object is correctly set up
    assert tlan.RF == []
    assert tlan.CHS == {}
    
    tlan.parse_line("AT 0 RFON")
    assert tlan.RF == [0.0]
    
    with pytest.raises(TarlanError):
        tlan.parse_line("AT 1 RFON")
    
    tlan.parse_line("AT 1 RFOFF")
    assert tlan.RF == [0.0, 1.0]
    
    with pytest.raises(TarlanError):
        tlan.parse_line("AT 1 RFOFF")
        
        
    erroneus_lines =  [
        "1 AT RFON",
        "RFON at 3"
        "at 3 CH6"
        ]
    # for line in erroneus_lines.split("\n"):
    for line in erroneus_lines:
        if len(line) == 0: continue
        with pytest.raises(TarlanError):
            tlan.parse_line(line)
    