#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 27 09:29:41 2024

"""
import pytest

from src.kstconfig.nco import Nco

def test_reading():
    # test of valid file (cp1l, ch1)
    
    file = """NCOPAR_VS       0.1
    %======================================
    % cp1l_ch1
    % LO1=812.0 MHz LO2=128.0 MHz
    %======================================
    NCO	0	 10.4	% f12
    NCO	1	 10.1	% f13
    NCO	2	 10.1	% f13
    NCO	3	 10.4	% f12"""
    
    freq = Nco.parse_nco(file)
    assert freq == [10.4, 10.1, 10.1, 10.4]
    
    
    # Test of bad file - missing first line
    badfile = """NCO	0	 10.4	% f12
    NCO	1	 10.1	% f13
    NCO	2	 10.1	% f13
    NCO	3	 10.4	% f12"""
    
    with pytest.raises(AssertionError):
        Nco.parse_nco(badfile)
    
    # Test of bad file - wrong first line
    faultyfile = """NCOPAR_VS       0.2
    %======================================
    % cp1l_ch1
    % LO1=812.0 MHz LO2=128.0 MHz
    %======================================
    NCO	0	 10.4	% f12
    NCO	1	 10.1	% f13
    NCO	2	 10.1	% f13
    NCO	3	 10.4	% f12"""
    
    with pytest.raises(AssertionError):
        Nco.parse_nco(faultyfile)
        
    # Test of bad file - forgot comment %
    faultyfile2 = """NCOPAR_VS       0.1
    %======================================
    % cp1l_ch1
    % LO1=812.0 MHz LO2=128.0 MHz
    %======================================
    NCO	0	 10.4	% f12
    NCO	1	 10.1	 f13
    NCO	2	 10.1	% f13
    NCO	3	 10.4	% f12"""
    
    with pytest.raises(AssertionError):
        Nco.parse_nco(faultyfile2)
        
    # Test of bad file - Wrong number
    faultyfile3 = """NCOPAR_VS       0.1
    %======================================
    % cp1l_ch1
    % LO1=812.0 MHz LO2=128.0 MHz
    %======================================
    NCO	0	 10.4	% f12
    NCO	1	 10.1	% f13
    NCO	2	 10.1	% f13
    NCO	4	 10.4	% f12"""
    
    with pytest.raises(AssertionError):
        Nco.parse_nco(faultyfile3)
        
    # Test of bad file - Frequency invalisd
    faultyfile4 = """NCOPAR_VS       0.1
    %======================================
    % cp1l_ch1
    % LO1=812.0 MHz LO2=128.0 MHz
    %======================================
    NCO	0	 10.4MHz	% f12
    NCO	1	 10.1MHz	% f13
    NCO	2	 10.1MHz	% f13
    NCO	4	 10.4MHz	% f12"""
    
    with pytest.raises(ValueError):
        Nco.parse_nco(faultyfile4)