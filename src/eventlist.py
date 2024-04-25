#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 09:52:47 2024

@author: jsatuit
"""
from collections import UserList

class TimedEvent:
    def __init__(self, time: float, event):
        self.time = time
        self.event = event
        
    def __lt__(self, other):
        return self.time < other.time
    
    def __str__(self):
        return f"{self.time}: {self.event}"
    
    def __repr__(self):
        return f"TimedEvent({self.time}, {self.event})"
        
        
        

class EventList(UserList):
    """
    List of timed events. Inherits from UserList to be able to use base
    list functions
    """
    def __setitem__(self, index, value):
        if not isinstance(value, TimedEvent):
            raise TypeError('only TimedEvent accepted')
        
        super().__setitem__(index, value)
            
    def insert(self, index, value):
        if not isinstance(value, TimedEvent):
            raise TypeError('only TimedEvent accepted')
        super().insert(index, value)
    
    def listof(self, attr: str):
        """
        Return list of the attribute `attr` of each TimeInterval.
        
        See other functions for examples.
        """
        return [getattr(event, attr) for event in self]
    
    @property
    def times(self) -> list[float]:
        """
        list with the time of each TimedEvent
        """
        return self.listof("time")
    
    @property
    def events(self) -> list[float]:
        """
        list of all events. That are all TimeEvent.events.
        """
        return self.listof("event")
