#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from typing import Union

from src import rtp
from src.timeInterval import TimeInterval
from src.const import km, µs, c

class Subcycle:
    """
    Handling timings for transmission, receiver channels. More properties will 
    follow?
    """
    def __init__(self, begin: float = 0, end: Union[float, bool] = False):
        self.transmits = []
        self.receive = {}
        self.rx_protection = []
        self.prop = {}
        
        self._begin = begin
        self._end = end
        
    @property
    def end(self):
        time = 0
        if self._end:
            time = self._end
        else:
            raise NotImplementedError("""Loop through all transmits, receives 
                                      and other settings and use the last one""")
        return time
    @property
    def begin(self):
        return self._begin
                                      
    def add_time(self, name: str, time: TimeInterval):
        """
        Adds TimeInterval to relevant attribute of Subcycle.
        
        :param name: declares what the interval is for: Possibilities are:
            - "transmission"/"t" - transmission
            - "ch<some number>" - reception in channel with specified number
        :type name: str
        :param time: interval with on and off time of attribute
        :type time: TimeInterval

        """
        
        # Dont care about large or small letters
        name = name.casefold()
        
        
        if name in ["transmission", "t", "rf"]:
            self.transmits.append(time)
        elif name.startswith("ch"):
            
            channel = int(name[2:])
            
            if channel not in self.receive:
                self.receive[channel] = []
            self.receive[channel].append(time)
        elif "prot" in name:
            self.rx_protection.append(time)
        else:
            if name not in self.prop:
                self.prop[name] = []
            self.prop[name].append(time)
            
    def plot(self, show_rec_if_send: bool = True):
        
        plot_interval = TimeInterval(self.begin, self.end)
        
        plt.figure()
        plt.grid(which = 'major')
        for transmit in self.transmits:
            rtp.plot_transmit(transmit, plot_interval)
        
        cols = ["black", "red", "green", "orange", "brown", "grey"]
        for i, receives in enumerate(self.receive.values()):
            for receive in receives:
                if not receive.within_any(self.rx_protection):
                    print(receive, self.rx_protection)
                    rtp.plot_receive(receive, plot_interval, color=cols[i])
                else:
                    print("noplot")
            
        # Hard-coded, not good, but as long as we have no reception, 
        # we cant do better...
        plt.ylim(0, 1000)
        # for ch in self.receive_channels:
        #     for receive in ch:
        #             plot_receive(receive, self.instruction_cycle)
        # plot_add_range_label(rmin)
        # plot_add_range_label(rmax)
        
class Experiment:
    """
    Handling timings for transmitter and receiver channels
    """
    def __init__(self):
        self.subcycles = []
        
    def add_subcycle(self, subcycle: Subcycle):
        self.subcycles.append(subcycle)
    
    
    # def plot(self, subcycle: int = 1):
        
    #     if subcycle <= 0 and subcycle > len(self.subcycles):
    #         raise ValueError("Select a subcycle between 1 and {len(self.subcycles)}, not {subcycle}")
        
    #     plot_interval = self.subcycles[subcycle-1]
        
    #     plt.figure()
    #     plt.grid(which = 'major')
    #     for transmit in self.transmits:
    #         if transmit.within(plot_interval):
    #             rtp.plot_transmit(transmit, plot_interval)
        
    #     cols = ["black", "red", "green", "orange", "brown", "grey"]
    #     for i, receives in enumerate(self.receive.values()):
    #         for receive in receives:
    #             if receive.within(plot_interval):
    #                 rtp.plot_receive(receive, plot_interval, color=cols[i])
            
    #     # Hard-coded, not good, but as long as we have no reception, 
    #     # we cant do better...
    #     plt.ylim(0, 1000)
    #     # for ch in self.receive_channels:
    #     #     for receive in ch:
    #     #             plot_receive(receive, self.instruction_cycle)
    #     # plot_add_range_label(rmin)
    #     # plot_add_range_label(rmax)
        
