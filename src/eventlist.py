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
        self._list.insert(index, value)
        
        
    
    