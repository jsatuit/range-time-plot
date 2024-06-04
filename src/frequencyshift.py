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
