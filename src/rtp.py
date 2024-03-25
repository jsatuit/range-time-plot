

import numpy as np
import matplotlib.pyplot as plt


µs = 1e-6

"Speed of light"
c = 3e8

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

def plot_transmit(tx_interval, plot_interval, h_radar=0, elevation = 90):
    
    plt.figure()
    # Nodes of first line
    line1x = tx_interval.begin + np.array((0 , plot_interval.length))
    line1y = h_radar + np.array((0 , np.sin(np.deg2rad(elevation))*plot_interval.length*c))
    
    line2x = tx_interval.end + np.array((0 , plot_interval.length))
    line2y = h_radar + np.array((0 , np.sin(np.deg2rad(elevation))*plot_interval.length*c))
    print(line1y-line2y)
    # Plot beginning of pulse
    plt.plot(line1x, line1y, 'b-')
    # Plot end of pulse
    plt.plot(line2x, line2y, 'b-')
    plt.xlim(plot_interval.as_tuple)


if __name__ == '__main__':
    # Using Beata UHF as example
    transmit = TimeInterval(82,722)*µs
    receive = TimeInterval(1037, 5357)*µs
    cycle = TimeInterval(0,5580)*µs
    
    plot_transmit(transmit, cycle)
    