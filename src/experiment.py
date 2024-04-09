#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from src.timeInterval import TimeInterval
from src import rtp

from src.const import km, µs, c

class Experiment:
    """
    Handling timings for transmitter and receiver channels
    """
    def __init__(self):
        self.transmits = []
        self.receive_channels = []
        self.instruction_cycle = TimeInterval(0,0)
        
        
    def add_transmit_time(self, time: TimeInterval):
        # TODO: Check for overlapping 
        # TODO: Sort
        self.transmits += [time]
    # TODO: Add receiver channels. But here we will have more than one.
    
    def add_stop_time(self, time: float):
        self.instruction_cycle.end = time
    
    def plot(self):
        
        plt.figure()
        plt.grid(which = 'major')
        for transmit in self.transmits:
            rtp.plot_transmit(transmit, self.instruction_cycle)
            
        # Hard-coded, not good, but as long as we have no recetion, we cant do better...
        plt.ylim(0, 1000)
        plt.xlim(0, self.transmits[1].begin/µs)
        # for ch in self.receive_channels:
        #     for receive in ch:
        #             plot_receive(receive, self.instruction_cycle)
        # plot_add_range_label(rmin)
        # plot_add_range_label(rmax)
        
