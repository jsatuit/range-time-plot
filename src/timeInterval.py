#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 14:05:51 2024

@author: jsatuit
"""
# Requires python 3.11 or newer
from typing import Self


class OverlapError(Exception):
    """
    Exception raised when transmit and receive TimeIntervals overlap.
    """
    def __init__(self, *args):
        super().__init__("The radar transmits while receiving!", args)

class TimeInterval:
    """
    
    Handling one begin and end of the time the transmitter/receiver channel is on.
    
    :param begin: Begin of interval
    :param end: End of interval. Must be after begin
    :raises ValueError: when begin of interval comes after end
        
    """
    def __init__(self, begin: float = 0.0, end: float = 0):
        if end < begin:
            raise ValueError("Start of interval must come before end")
        self.begin = begin
        self.end = end

    def __mul__(self, num: float) -> Self:
        """
        Multiplies interval begin and end times with num.
        
        :param num: Number to multiply with
        :return: TimeInterval(begin*num, end*num)

        """
        
        return TimeInterval(self.begin*num, self.end*num)
        
    def __repr__(self) -> str:

        return f"TimeInterval({self.begin}, {self.end})"
    
    def __eq__(self, other: Self) -> bool:
    
        return self.begin == other.begin and self.end == other.end
    
    @property
    def length(self) -> float:
        """
        Length/duration of interval
        """
        return self.end-self.begin
    
    @property
    def as_tuple(self) -> tuple[float, float]:
        return (self.begin, self.end)
    
    def overlaps_with(self, other: Self) -> bool:
        """
        Checks if TimeInterval overlaps with other TimeInterval
        
        :param other: TimeInterval to check overlap with
        :type other: TimeInterval
        :return: If the intervals overlap
        :rtype: bool

        """

        overlap: bool = True
        if self.begin <= other.end and self.end <= other.begin:
            overlap = False
        elif other.begin <= self.end and other.end <= self.begin:
            overlap = False
        
        
        return overlap
    def check_overlap(self, other: Self):
        """
        Checks if TimeInterval overlaps with other TimeInterval. If so, 
        an OverlapError is raised
        
        :param other: TimeInterval to check overlap with
        :type other: TimeInterval
        :raises OverlapError: When intervals overlap
        :rtype: bool

        """
        if self.overlaps_with(other):
            raise OverlapError
        