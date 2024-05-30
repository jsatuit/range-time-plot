#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import difflib

from typing import Union

from src.expplot import Expplot, calc_nearest_range, calc_furthest_full_range
from src.tlan.tarlan import Tarlan
from src.timeInterval import TimeInterval, TimeIntervalList
from src.elan.elan import Eros, filefinder
from src.eventlist import EventList
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
        self.baudlengths = []
        self.phaseshifts = EventList()

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

    def plot(self, plot=None, rangelims: bool = False) -> None:
        """
        Plot reached ranges and transmitter/receiver states for single subcycle.

        :param plot: If given Expplot, everything is plotted into given Expplot object. 
            If None, a new plot is created, defaults to None
        :type plot: Expplot | None, optional
        :param bool, optional rangelims: Show nearest and furthest ranges as
            axis ticks. default False.

        """

        if plot is None:
            plot = Expplot(TimeInterval(self.begin, self.end))
            plot.xlim()

        # Make range-time plot
        for transmit in self.transmits:
            plot.transmit("RF", transmit)
        for i, (ch, receives) in enumerate(self.receive.items()):
            for receive in receives:
                if not receive.within_any(self.rx_protection):
                    plot.receive("CH"+str(ch), receive)
        plot.state("RF", self.transmits.lengths, self.transmits.begins)
        plot.phase(self.phaseshifts, self.transmits)
        if rangelims:
            # Calculate nearest and furthest range for all transmit–receive pairs
            nearest = []
            furthest = []
            for i, transmit in enumerate(self.transmits):
                for (ch, receives) in self.receive.items():
                    for receive in receives:
                        nearest.append(calc_nearest_range(transmit, receive,
                                                          self.baudlengths[i]))
                        furthest.append(calc_furthest_full_range(transmit,
                                                                 receive,
                                                                 self.baudlengths[i]))
            for ran in nearest:
                plot.add_range_label(ran)
            for ran in furthest:
                plot.add_range_label(ran)

        # Plot state properties of experiment
        for i, (ch, receives) in enumerate(self.receive.items()):
            plot.state("CH"+str(ch), receives.lengths, receives.begins)
        if self.rx_protection:
            plot.state("Rx protector", self.rx_protection.lengths,
                       self.rx_protection.begins)
        for name, iv in self.prop.items():
            plot.state(name, iv.lengths, iv.begins)


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
    def from_tlan(cls, filename: str):
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

        expname = os.path.splitext(os.path.split(filename)[1])[0]
        exp = cls(expname)

        tlan = Tarlan(filename)

        for i, subcycle_interval in enumerate(tlan.subcycle_list.intervals):
            subcycle = Subcycle(subcycle_interval.begin, subcycle_interval.end)

            for stream in tlan.subcycle_list.data_intervals[i]:
                if len(stream) == 0:
                    continue
                for data_interval in tlan.subcycle_list.data_intervals[i][stream].intervals:
                    subcycle.add_time(stream, data_interval)
            subcycle.phaseshifts, subcycle.baudlengths = tlan.phaseshifts(i)
            exp.add_subcycle(subcycle)

        return exp

    @classmethod
    def from_eiscat_kst(cls, filename: str, radar="UHF"):
        """Load experiment file and convert to Experiment.

        This is a wrapper function for loading from tlan or from elan file.
        Which ine is called is determined by the file ending. File name without 
        ending is interpreted as .elan

        For arguments, see from _tlan and from_elan

        """
        if filename.endswith(".tlan"):
            return Experiment.from_tlan(filename)
        else:
            return Experiment.from_elan(filename)

    @classmethod
    def from_elan(cls, filename: str, radar: str = 'UHF'):
        """
        Load experiment file and convert to Experiment.

        This is done by parsing the commands that would be run if the user typed
        "runexperiment <filename> <timestec> <some args>" in an real EROS console.

        :param str filename: Path of elan file to load. The filename may have 
            the ending .elan or the ending may be be left out. If the file is 
            not found, python will look into "/kst/exp/filename" and "kst/exp/filename"
        :param str radar: Site to plot the experiment for. Possibles are "UHF", 
            "VHF", "ESR", "KIR", "SOD"
        :raises RuntimeError: If radar controller is not resetted correctly 
            at end of tlan file.
        :raises RuntimeWarning: if transmitter is constantly off.
        :return: Object containing properties of the experiment.
        :rtype: Experiment


        """
        (directory, expname, path) = filefinder(filename)
        exp = cls(expname)

        # Parse elan
        eros = Eros(radar)
        eros(f"runexperiment {path} lm scan_pattern Country 90.0")
        
        tlan = Tarlan(os.path.join(directory, eros.py_get_tlan(directory)),
                      tuple(eros.py_get_lo(1)), tuple(eros.py_get_lo(2)))

        for i, subcycle_interval in enumerate(tlan.subcycle_list.intervals):
            subcycle = Subcycle(subcycle_interval.begin, subcycle_interval.end)

            for stream in tlan.subcycle_list.data_intervals[i]:
                if len(stream) == 0:
                    continue
                for data_interval in tlan.subcycle_list.data_intervals[i][stream].intervals:
                    subcycle.add_time(stream, data_interval)
            subcycle.phaseshifts, subcycle.baudlengths = tlan.phaseshifts(i)
            exp.add_subcycle(subcycle)

        return exp

    def plot(self, subcycles: list = []) -> None:
        """
        Plot multiple subcycles.

        Calls Subcycle.plot(plot) for every subcycle to plot

        :param subcycles: List of which subcycles to plot. Subcycles are 
            counted from one. Empty list means plot all subcycles, defaults 
            to plotting all. 
        :type subcycles: list, optional
        :raises ValueError: If invalid subcycle numbers are given.

        """

        for s in subcycles:
            if s <= 0:
                raise ValueError("Subcycle number must be larger than zero!")
            elif s > len(self.subcycles):
                raise ValueError(f"There are only {len(self.subcycles)}"
                                 + f"subcycles! You chose to plot subcycle {s},"
                                 + " which is too large")

        if len(subcycles) > 0:
            title = self.name + f", subcycles {subcycles}"
        else:
            title = self.name + "(whole cycle)"
            subcycles = list(range(1, len(self.subcycles) + 1))

        plot_interval = TimeInterval(self.subcycles[subcycles[0] - 1].begin,
                                     self.subcycles[subcycles[-1] - 1].end)
        plot = Expplot(plot_interval)
        plot.title(title)

        plot.xlim(plot_interval)

        for si in subcycles:
            self.subcycles[si-1].plot(plot)
