#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import tempfile
import os

from src.tarlan import µs, parse_line, TarlanError, Command, Tarlan


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
def test_command():
    cmd1 = Command(8*µs, "CH1", 32)
    cmd2 = Command(135*µs, "ALLOFF", 39)
    
    assert cmd1.t == 8e-6
    assert cmd1.cmd == "CH1"
    assert cmd1.line == 32
    
    assert cmd1 < cmd2
    assert cmd2 > cmd1
    
    assert eval(repr(cmd1)).__dict__ == cmd1.__dict__
    
    assert str(cmd1) == "32: 8.0 CH1"
    assert str(cmd2) == "39: 135.0 ALLOFF"
    
    
def test_tarlan():
    tlan = Tarlan()
    assert tlan.cycle.is_off
    assert tlan.subcycle_list.is_off
    for stream in tlan.streams.values():
        assert stream.is_off
    
    # No cycle has been started yet, so it should not be possible to execute 
    # commands
    with pytest.raises(TarlanError):
        tlan.exec_cmd(Command(1*µs, "CHQPULS", 3))
    
    tlan.cycle.turn_on(0, 1)
    tlan.subcycle_list.turn_on(0, 1)
    assert tlan.cycle.is_on
    assert tlan.subcycle_list.is_on
    
    assert tlan.streams["RF"].is_off
    tlan.exec_cmd(Command(10, "RFON", 7))
    assert tlan.streams["RF"].is_on
    tlan.exec_cmd(Command(20, "RFOFF", 7))
    assert tlan.streams["RF"].is_off
        
def test_tarlan_program():
    tarlan_program = b"""
    SETTCR 0
    AT 2 RXPROT,LOPROT
    AT 30 BEAMON,F5
    AT 40 RFON
    AT 220 RFOFF,BEAMOFF
    AT 230 RXPOFF
    AT 240 LOPOFF
    AT 350 CH1
    AT 1500 ALLOFF
    SETTCR 1505
    AT 2 RXPROT,LOPROT
    AT 30 BEAMON,F5
    AT 40 RFON
    AT 220 RFOFF,BEAMOFF
    AT 230 RXPOFF
    AT 240 LOPOFF
    AT 350 CH1
    AT 1500 ALLOFF
    SETTCR 0
    AT 3010 REP
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tlan") as file:
        file.write(tarlan_program)
    
    tlan = Tarlan(file.name)
    os.remove(file.name)
    
    subcycle_streams = tlan.subcycle_list.data_intervals
    subcycle_streams[0]["RF"].intervals[0].begin == pytest.approx(40*µs)
    subcycle_streams[0]["RF"].intervals[0].end == pytest.approx(220*µs)
    subcycle_streams[1]["RF"].intervals[0].begin == pytest.approx((40 + 1505)*µs)
    subcycle_streams[1]["RF"].intervals[0].end == pytest.approx((220 + 1505)*µs)
    