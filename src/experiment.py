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
        self.receive = {}
        self.instruction_cycle = TimeInterval(0,0)
        self.subcycles = []
        self.other_settings = {}
        
    def add_setting_time(self, name: str, time: TimeInterval):
        
        if hasattr(self, name):
            self.name.append(time)
        else:
            # Add setting if not existing
            if name not in self.other_settings:
                self.other_settings[name] = []
                
            self.other_settings[name].append(time)
            
    def add_transmit_time(self, time: TimeInterval):
        # TODO: Check for overlapping 
        # TODO: Sort
        self.transmits.append(time)
    
    def add_receive_time(self, channel: str, time: TimeInterval):
        if channel not in self.receive:
            self.receive[channel] = []
            
        self.receive[channel].append(time)
        
    def add_subcycle(self, time: TimeInterval):
        self.subcycles.append(time)
    
    def add_stop_time(self, time: float):
        self.instruction_cycle.end = time
    
    def plot(self, subcycle: int = 1):
        
        if subcycle <= 0 and subcycle > len(self.subcycles):
            raise ValueError("Select a subcycle between 1 and {len(self.subcycles)}, not {subcycle}")
        
        plot_interval = self.subcycles[subcycle-1]
        
        plt.figure()
        plt.grid(which = 'major')
        for transmit in self.transmits:
            if transmit.within(plot_interval):
                rtp.plot_transmit(transmit, plot_interval)
        
        cols = ["black", "red", "green", "orange", "brown", "grey"]
        for i, receives in enumerate(self.receive.values()):
            for receive in receives:
                if receive.within(plot_interval):
                    rtp.plot_receive(receive, plot_interval, color=cols[i])
            
        # Hard-coded, not good, but as long as we have no reception, 
        # we cant do better...
        plt.ylim(0, 1000)
        # for ch in self.receive_channels:
        #     for receive in ch:
        #             plot_receive(receive, self.instruction_cycle)
        # plot_add_range_label(rmin)
        # plot_add_range_label(rmax)
        
