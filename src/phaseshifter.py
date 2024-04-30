#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 11:52:30 2024

@author: jsatuit
"""
import numpy as np

from bisect import insort_left

from src.timeInterval import TimeInterval, TimeIntervalList
from src.eventlist import TimedEvent, EventList

class PhaseShifter():
    """Simulates behaviour of phase shifter"""
    def __init__(self):
        """Initialize phase shifter"""
        # Keep list private so that developers and users know that they should 
        # not manipulate the list so that it keeps being sorted.
        self._phase_shifts = []
        self._phases = []
        
    def set_phase(self, time: float, phase: float):
        """
        Set phase shifter to certain phase
        
        :param float time: Time of phase shift
        :param float phase: Phase to set to.

        """
        insort_left(self._phase_shifts, TimedEvent(time, phase))
        if phase not in self._phases:
            self._phases.append(phase)

    def restart(self):
        """Restarts phase shifter.
        
        Means that all saved content is deleted. Use this when data is copied, 
        for example at ethe end of a subcycle.
        """
        # If the list is empty, there is nothing to do and the phase shifter 
        # is off.
        if len(self._phase_shifts) > 0:
            last_phase = self._phase_shifts[-1].event
            self._phase_shifts = EventList()
            self.set_phase(0, last_phase)
        
    def PHA0(self, time: float, line: int = 0):
        """
        Set phase shifter to 0 degree.
        
        :param float time: Time of phase shift
        :param int line: Line of command in tlan file. Not in use
        """
        self.set_phase(time, 0)
        
    def PHA180(self, time: float, line: int = 0):
        """
        Set phase shifter to 180 degree.
        
        :param float time: Time of phase shift
        :param int line: Line of command in tlan file. Not in use
        """
        self.set_phase(time, 180)
    
    # def intervals_within(self, interval: TimeInterval) -> dict[float, TimeIntervalList]:
    #     """
    #     Give intervals of the times when phaseshifter inserts phase shifts.
        
    #     Output intervals are within the specified interval.
        
    #     :param interval: Interval the output should be within
    #     :type interval: TimeInterval
    #     :return: dictionary of phaseshift – TimeIntervalList pairs.
    #     :rtype: dict[float, TimeIntervalList]

    #     """
    #     d = {}
    #     for phase in self._phases:
    #         for phase_shift in self._phase_shifts:
    @property
    def phase_shifts(self):
        "List of TimedEvents contaning the phase shifts"
        return self._phase_shifts
    
    def phase_shifts_within(self, interval: TimeInterval, 
                            tx_intervals: TimeIntervalList | None = None
                            ) -> EventList | tuple[EventList, list[float]]:
        """List of TimedEvents contaning the phase shifts within interval.
        
        The last phase shift before the interval is also returned.
        
        Also returns list of (estimated) baud lengths if transmit intervals are 
        given.
        
        :param interval: interval which the phases shifts should be inside of.
        :type interval: TimeInterval
        :param tx_intervals: transmit intervals. If wanted to estimate baud 
            lengths, these must be given, defaults to None
        :type tx_intervals: TimeIntervalList or None, optional
        :return: A list of the phase shifts within the interval. If 
            tx_intervals is given, also a list of baud lengths is returned.
        :rtype: EventList[, list[float]]

        """
        phase_shifts = EventList()
        
        # Tells if we are above the lower limit of the interval
        begun = False
        # Keeps the index of first phase shift within the interval
        first_index = None
        for i, shift in enumerate(self.phase_shifts):
            # Keep first index for adding the phase shift before thr first
            # because the phaseshift may still be the first in this subcycle.
            if not begun:
                first_index = i
            
            # Actiual appending
            if shift.time >= interval.begin and shift.time <= interval.end:
                begun = True
                phase_shifts.append(shift)
                
        # Add the last phase shift from before the interval
        if first_index > 0:
            last_shift = TimedEvent(interval.begin, 
                                    self.phase_shifts[first_index - 1].event)
            phase_shifts.insert(0, last_shift)
        
        if tx_intervals is not None:
            baud_lengths = \
                [self.estimate_baud_length(interval) for interval in tx_intervals]
            
            return phase_shifts, baud_lengths
        else:
            return phase_shifts
    
    def estimate_baud_length(self, interval: TimeInterval) -> float:
        """
        Estimate baud length within transmit interval.
        
        Baud length is estimated by finding the greatest common divisor of the 
        time between the phase shifts in the transmit pulse.
        
        :param interval: transmit interval
        :type interval: TimeInterval
        :return: baud length
        :rtype: float

        """
        # Timepoints where phase is shifted
        tshifts = self.phase_shifts_within(interval).times
        
        # Length of the time the phase shifter is in one state
        tlen = np.diff(tshifts)
        
        # Change subcycle time to integers showing the time in nanoseconds.
        # This is much better than the radar controller ca do, so there should
        # be problems with too bad accuracy. NO CHECKS ARE MADE!
        tlenns = np.rint(tlen*1e9).astype(int)
        
        return np.gcd.reduce(tlenns)/1e9
    
    def as_line(self, interval: TimeInterval):
        phase_shifts = self.phase_shifts_within(interval)
        
        t = np.asarray(phase_shifts.times)
        p = np.asarray(phase_shifts.events)
        
        tl = np.hstack([t[0] + np.repeat(t[1:], 2)])
        pl = np.hstack([np.repeat(t[0:-1], 2) + p[-1]])
        
        return tl, pl
        
        