#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.tarlan import parse_line, TarlanError

import pytest

def test_parse_line():
    
    erroneus_lines =  [
        "1 AT RFON",
        "RFON at 3"
        "at 3 CH6"
        ]
    # for line in erroneus_lines.split("\n"):
    for line in erroneus_lines:
        if len(line) == 0: continue
        with pytest.raises(TarlanError):
            parse_line(line)
    
    # cmds = ["CHQPULS", "RXSYNC", "NCOSEL0", "AD2L", "AD2R", "STFIR"]
    # assert parse_line("AT 0.9 "+ ",".join(cmds)) == (0.9, cmds)
    