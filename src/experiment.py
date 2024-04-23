#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import matplotlib.pyplot as plt

from typing import Union

from src.expplot import Expplot
from src.tarlan import Tarlan
from src.timeInterval import TimeInterval, TimeIntervalList
from src.const import km, µs, c

class Subcycle:
    """
    Handling timings for transmission, receiver channels. More properties will 
    follow?
    """
    def __init__(self, begin: float = 0, end: Union[float, bool] = False):
        self.transmits = TimeIntervalList()
        self.receive = {}
        self.rx_protection = TimeIntervalList()
        self.prop = {}
        
        self._begin = begin
        self._end = end
        self.name = ""
        
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
                self.receive[channel] = TimeIntervalList()
            self.receive[channel].append(time)
        elif "prot" in name:
            self.rx_protection.append(time)
        else:
            if name not in self.prop:
                self.prop[name] = TimeIntervalList()
            self.prop[name].append(time)
            
    def plot(self, ax = None) -> None:
        
        plot = Expplot(TimeInterval(self.begin, self.end))
        
        
        # plot_interval = TimeInterval(self.begin, self.end)
        
        # if ax is None:
        #     fig = plt.figure(layout="constrained")
        #     ax = fig.subplots(2, sharex=True, squeeze=True)
        #     fig.suptitle(self.name)
        # plt.subplot(2,1,1)
        # ax[0].grid(which = 'major')
        for transmit in self.transmits:
            plot.transmit(transmit)
        
        cols = ["black", "red", "green", "orange", "brown", "grey"]
        for i, receives in enumerate(self.receive.values()):
            for receive in receives:
                if not receive.within_any(self.rx_protection):
                    plot.receive(receive, color = cols[i])
            

        # ax[0].set_ylim(0, 1000)

        plot.state("RF", self.transmits.lengths, self.transmits.begins)
        # for i, (ch, receives) in enumerate(self.receive.items()):
        #     expplot.plot_setting(ax[1], "CH"+str(ch), receives.lengths, receives.begins, 
        #                      plot_interval, color = cols[i])
        # if self.rx_protection:
        #     expplot.plot_setting(ax[1], "Rx protector", self.rx_protection.lengths,
        #                      self.rx_protection.begins, plot_interval)
        # for name, iv in self.prop.items():
        #     expplot.plot_setting(ax[1], name, iv.lengths, iv.begins, plot_interval)
        plot.xlim()
        
        
class Experiment:
    """
    Handling timings for transmitter and receiver channels
    """
    def __init__(self, name: str = ""):
        self.subcycles = []
        self.name = name
        
    def add_subcycle(self, subcycle: Subcycle):
        self.subcycles.append(subcycle)
        self.subcycles[-1].name = f"{self.name}: subcycle {len(self.subcycles)}"
    
    @classmethod
    def from_eiscat_kst(cls, filename: str):
        """
        Load experiment file and convert to Experiment.
        
        :param filename: Path of tlan file to load.
        :type filename: str
        :raises RuntimeError: If radar controller is not resetted correctly 
            at end of file.
        :raises RuntimeWarning: if transmitter is constantly off.
        :return: Object containing properties of the experiment.
        :rtype: Experiment

        """
        exp = cls(os.path.basename(filename).split(".")[0])
        
        tlan = Tarlan(filename)
        
        for i, interval in enumerate(tlan.subcycle_list.intervals):
            subcycle = Subcycle(interval.begin, interval.end)
            
            for stream in tlan.subcycle_list.data_intervals[i]:
                if len(stream) == 0:
                    continue
                for interval in tlan.subcycle_list.data_intervals[i][stream].intervals:
                    subcycle.add_time(stream, interval)
            
            exp.add_subcycle(subcycle)

        
        return exp
    
    def plot(self, subcycles: list = []):
        for s in subcycles:
            if s <= 0:
                raise ValueError("Subcycle number must be larger than zero!")
            elif s > len(self.subcycles):
                raise ValueError(f"There are only {len(self.subcycles)}" \
                            + f"subcycles! You chose to plot subcycle {s},"\
                            + " which is too large")
        
        if len(subcycles) > 0:
            title = self.name + f", subcycles {subcycles}"
        else:
            title = self.name + "(whole cycle)"
            subcycles = list(range(len(self.subcycles)))
        
        
        
        fig = plt.figure()
        ax = fig.subplots(2, sharex=True, squeeze=True)
        fig.suptitle(title)
        
        for si in subcycles:
            self.subcycles[si-1].plot(ax)
        
        
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
