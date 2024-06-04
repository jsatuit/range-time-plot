#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 14:14:31 2024

"""
from typing import Self
from sortedcontainers import SortedDict

from src.timeInterval import TimeInterval


class FrequencyList(SortedDict):
    @property
    def frequencies(self):
        return list(dict.fromkeys(self.values()))

    def shifts_within(self, interval: TimeInterval) -> Self:
        """List of TimedEvents contaning the frequency shifts within interval.

        The frequency used when interval starts is also returned: Not only those shifts that happen after interval starts.

        Also returns list of (estimated) baud lengths if transmit intervals are 
        given.

        :param interval: interval which the phases shifts should be inside of.
        :type interval: TimeInterval
        :param tx_intervals: transmit intervals. If wanted to estimate baud 
            lengths, these must be given, defaults to None
        :return: A list of the frequencies that occur within the interval.
        :rtype: EventList

        """
        i0 = self.bisect_right(interval.begin) - 1
        if i0 < 0:
            raise ValueError(
                "TimeInterval begins before first frequency is defined!")
        i1 = self.bisect_left(interval.end)

        times = self.keys()
        freqs = self.values()
        frequencies = FrequencyList()
        frequencies[interval.begin] = freqs[i0]
        for i in range(i0 + 1, i1):
            frequencies[times[i]] = freqs[i]
            # FOrtsett her: Sett inn frekvensskiftene som trengs.
            print(self.peekitem(i))

        return frequencies

    def as_line(self, interval: TimeInterval) -> tuple[list, list]:
        """
        Coordinates of a line connecting the phase shifts within an interval
        
        That is a list of x coordinates and a list of y coordinates which 
        respectively describes the time and phases of the phase shifts
        
        Example:
        180        x----------x     x----   etc.
                   |          |     |
        0   -x-----x          x-----x
             0     6          17    25   
        
        gives
        [0, 6, 6, 17, 17, 25, 25, ...]
        and
        [0, 0, 180, 180, 0, 0, 180, ...]
        
        (Not used at current)
        
        :param interval: Interval the shifts should be within
        :type interval: TimeInterval
        :return: lists of coordinates
        :rtype: tuple[list[float], list[float]]

        """
        shifts = self.shifts_within(interval)
        
        x = [item for item in shifts.keys() for _ in range(2)][1:] + [interval.end]
        y = [item for item in shifts.values() for _ in range(2)]
        
        return x, y