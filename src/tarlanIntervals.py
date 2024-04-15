#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from src.tarlanError import TarlanError
from src.timeInterval import TimeInterval

class IntervalList:
    """
    Contain intervals for when data streams are enabled. 
    Intervals may be open in contrast to TimeInterval, which must contain 
    closed intervals
    """
    
    def __init__(self, name: str):
        """
        
        :param name: Name of datastream
        :type name: str

        """
        self.name = name
        self._streams = []
    
    @property
    def state(self) -> bool:
        """
        
        :raises RuntimeError: if the last stream contains more than one on and 
            off value(should never happen, but who knows...)
        :return: state (on/off) of data stream.
        :rtype: bool

        """
        
        if len(self._streams) == 0:
            on = False
        elif len(self._streams[-1]) == 0:
            on = False
        elif len(self._streams[-1]) == 1:
            on = True
        elif len(self._streams[-1]) == 2:
            on = False
        else:
            raise RuntimeError("There is something bad with the streams:"+
                               str(self._streams))
        return on
    
    @property
    def is_off(self) -> bool:
        """
        If stream is turned off
        
        :type: bool

        """
        return not self.state
    
    @property
    def is_on(self) -> bool:
        """
        If stream is turned on
        
        :type: bool

        """
        return self.state
    
    def turn_on(self, time: float, line: int) -> None:
        """
        Turn on data stream.
        
        :param time: time at which to turn on the stream
        :type time: float
        :param line: line in the tlan file. Used for error handling only.
        :type line: int
        :raises TarlanError: if stream is on already

        """
        if self.is_off:
            self._streams.append([time])
        else:
            raise TarlanError(f"Data stream {self.name} is already on!", line)
    
    def turn_off(self, time: float, line: int):
        """
        Turn off data stream.
        
        :param time: time at which to turn off the stream
        :type time: float
        :param line: line in the tlan file. Used for error handling only.
        :type line: int
        :raises TarlanError: if stream is off already
        
        """
        if self.is_on:
            self._streams[-1].append(time)
        else:
            raise TarlanError(f"Data stream {self.name} is already off!", line)
            
    @property
    def nstreams(self) -> int:
        """
        Number of streams
        
        :type: int

        """
        return len(self._streams)
    
    def __len__(self) -> int:
        """
        Number of streams
        
        :type: int

        """
        return self.nstreams
    
    @property
    def intervals(self) -> list[TimeInterval]:
        """
        Return the on-time of the streams as a list of TimeIntervals
        
        :type: list[TimeInterval]

        """
        if self.is_on:
            raise RuntimeError("Stream is on. Cant return open intervals.")
        iv = []
        for i in range(self.nstreams):
            iv.append(TimeInterval(*self._streams[i]))
        return iv

    @property
    def last_turn_off(self) -> float:
        """
        Last time when the stream was turned off
        
        :raises RuntimeError: If there stream has not been turned off yet.
        :type: float

        """
        if self.nstreams == 0:
            raise RuntimeError("Stream has not been turned on yet!")
        elif self.is_off:
            return self._streams[-1][1]
        elif self.nstreams == 1:
            # Is on too
            raise RuntimeError("Stream is on, but has not been turned off yet!")
        else:
            return self._streams[-2][1]
   