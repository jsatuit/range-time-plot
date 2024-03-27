

import numpy as np
import matplotlib.pyplot as plt


µs = 1e-6
km = 1e3

c = 3e8
"Speed of light [m/s]"

class TimeInterval:
    """
    
    Handling one begin and end of the time the transmitter/receiver channel is on.
    """
    def __init__(self, begin=0.0, end=0):
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

def plot_transmit(tx_interval, plot_interval, **kwargs):
    """
    Plots transmit beam position
    
    :param signal_interval: Interval of signal being transmitted
    :type signal_interval: TimeInterval
    :param TimeInterval plot_interval: Axis limits of time axis
    
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
    :param float or int, optional d: Direction of beam. +1 Transmit, -1 receive, default transmit
    
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
    

if __name__ == '__main__':
    # Using Beata UHF as example
    transmit = TimeInterval(82,722)*µs
    receive = TimeInterval(1037, 5357)*µs
    cycle = TimeInterval(0,5580)*µs
    
    plt.figure()
    plot_transmit(transmit, cycle)
    plot_receive(receive, cycle)
    