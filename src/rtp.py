
from typing import Self
import numpy as np
import matplotlib.pyplot as plt


µs = 1e-6
km = 1e3

c = 3e8
"Speed of light [m/s]"
class OverlapError(Exception):
    """
    Exception raised when transmit and receive TimeIntervals overlap.
    """
    def __init__(self, *args):
        super().__init__("The radar transmits while receiving!", args)

class TimeInterval:
    """
    
    Handling one begin and end of the time the transmitter/receiver channel is on.
    """
    def __init__(self, begin: float = 0.0, end:float = 0):
        if end < begin:
            raise ValueError("Start of interval must come before end")
        self.begin = begin
        self.end = end

    def __mul__(self,other):
        return TimeInterval(self.begin*other, self.end*other)
        
    def __repr__(self):
        return f"TimeInterval({self.begin}, {self.end})"
    
    @property
    def length(self):
        return self.end-self.begin
    
    @property
    def as_tuple(self):
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
        
class Experiment:
    """
    Handling timings for transmitter and receiver channels
    """
    def __init__(self):
        self.transmits = []
        self.receive_channels = []
    def add_transmit_time(self,time):
        # TODO: Check for overlapping 
        # TODO: Sort
        self.transmits += [time]
    # TODO: Add receiver channels. But here we will have more than one.


def calc_nearest_range(tx_interval: TimeInterval, rx_interval: TimeInterval, 
                       baud_length: float, v: float = c) -> float:
    """
    Calculates the nearest range the experiment can measure. Since only one baud 
    will be measured at this range, the performance at this range will be low.
    
    :param tx_interval: Transmit interval
    :param rx_interval: Receive interval
    :param baud_length: baud length of experiment
    :param v: Speed of beam, default speed of light
    :return: Nearest range gate. 
    

    """
    
    rx_interval.check_overlap(tx_interval)
    
    
    # Traveltime to nearest range gate
    dt = rx_interval.begin-tx_interval.end+baud_length
    
    # Time travelled is the time light uses back and forth
    r = v*dt/2
    
    return r

def calc_furthest_full_range(tx_interval: TimeInterval, rx_interval: TimeInterval, 
                        baud_length: float, v: float = c) -> float:
    """
    Calculates the furthest range the experiment measures. This is the last range
    where the receiver «sees» the *whole* transmit passing through.
    
    :param tx_interval: Transmit interval
    :param rx_interval: Receive interval
    :param baud_length: baud length of experiment
    :param v: Speed of beam, default speed of light
    :return: Furthest range gate. 
    """
    
    rx_interval.check_overlap(tx_interval)
    
    # Traveltime to furtherst range gate
    dt = rx_interval.end-tx_interval.end
    
    # Time travelled is the time light uses back and forth
    r = v*dt/2
    
    return r

def plot_transmit(tx_interval: TimeInterval, plot_interval: TimeInterval, **kwargs):
    """
    Plots transmit beam position
    
    :param signal_interval: Interval of signal being transmitted
    :param plot_interval: Axis limits of time axis
    
    Other keyword arguments go to plotting punctions
    
    """
    plot_t_r(tx_interval, plot_interval, v=c, color='blue', **kwargs)
    
def plot_receive(rx_interval, plot_interval, **kwargs):
    """
    Plots receive beam position
    
    :param TimeInterval signal_interval: Interval of signal being received
    :param TimeInterval plot_interval: Axis limits of time axis
    
    Other keyword arguments go to plotting punctions
    
    """
    plot_t_r(rx_interval, plot_interval, v=c, d = -1, color='red', **kwargs)
    
def plot_t_r(signal_interval, plot_interval, v=c, d = 1, **kwargs):
    """
    Plots transmit or receive beam position
    
    :param TimeInterval signal_interval: Interval of signal being transmitted/received
    :param TimeInterval plot_interval: Axis limits of time axis
    :param float or int, optional v: Velocity of beam, default light speed
    :param float or int, optional d: Direction of beam. +1 Transmit, -1 receive, defaults to transmit
    
    Other keyword arguments go to plotting punctions
    
    """#Returns#Raises
    # Nodes of first line
    line1x = signal_interval.begin + np.array((0 , d*plot_interval.length))
    line1y = np.array((0 , plot_interval.length*v))
    
    line2x = signal_interval.end + np.array((0 , d*plot_interval.length))
    line2y = np.array((0 , plot_interval.length*v))
    # Plot beginning of pulse
    plt.plot(line1x, line1y/km, **kwargs)
    # Plot end of pulse
    plt.plot(line2x, line2y/km, **kwargs)
    plt.xlim(plot_interval.as_tuple)
    plt.xlabel("Time [µs]")
    plt.ylabel("Range [km]")

def plot_add_range(r, label = ""):
    """
    Adds a label to a certain range.
    
    :param r: range [m]
    :type r: float
    :param label: Label text. If empty, range in km is used. Defaults to range in km
    :type label: str, optional

    """
    pass
    

if __name__ == '__main__':
    # Using Beata UHF as example
    transmit = TimeInterval(82,722)*µs
    "Transmit interval of beata UHF experiment"
    receive = TimeInterval(1037, 5357)*µs
    cycle = TimeInterval(0,5580)*µs
    Tb = 10*µs
    rmin = calc_nearest_range(transmit, receive, Tb)
    rmax = calc_furthest_full_range(transmit, receive, Tb)
    print(rmin," ",rmax)
    
    plt.figure()
    plt.grid()
    plot_transmit(transmit, cycle)
    plot_receive(receive, cycle)
    