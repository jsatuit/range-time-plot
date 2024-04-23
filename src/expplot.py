

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mc


if __name__ == '__main__':
    import sys
    sys.path.append("..") # Adds current directory to python modules path.
    
from typing import Union
from src.timeInterval import TimeInterval
from src.const import km, µs, c

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
class Expplot:
    """
    An interface to matplotlib specialised for plotting experiments 
    (transmit/receive beams)
    """
    def __init__(self, plot_interval: TimeInterval, rmax: float = 1e6):
        self.fig = plt.figure()
        self.ax = self.fig.subplots(2, sharex=True, squeeze=True)
        self.ax[0].grid(which = 'major')
        self.ax[0].set_ylim(0, rmax/km)
        self.ax[1].invert_yaxis()
        self.plot_interval = plot_interval
        
        self.available_colours = list(mc.TABLEAU_COLORS)
        # Dictionary of name/is/property – colour pairs
        self.cols = {}
        
    def get_colour(self, name: str) -> str:
        """
        Get colour for desired parameter.
        
        Assigns a new colour if needed. There is a maximum of assignable 
        colours since matplotlibs default colours are used. These are limited.
        
        :param name: parameter name
        :type name: str
        :raises RuntimeError: if a new colour is assigned but there is no new 
            colour to take.
        :return: colour
        :rtype: str

        """
        if name in self.cols.keys():
            colour = self.cols[name]
        else:
            try:
                colour = self.available_colours.pop(0)
            except IndexError:
                raise RuntimeError("Ran out of colours!")
            self.cols[name] = colour
        return colour
        
    def title(self, title: str):
        """
        Set supertitle to figure
        
        :param title: Title string
        :type title: str

        """
        self.fig.suptitle(title)
        
    def xlim(self, interval: Union[TimeInterval, None] = None):
        """
        Set x axes limits.
        
        :param TimeInterval | None interval: x axes limits as a TimeInterval
        
        """
        if interval is None:
            interval = self.plot_interval
            
        for ax in self.ax:
            self.ax[0].set_xlim((interval/µs).as_tuple)
        
        
    def add_beam(self, name: str, interval: TimeInterval, v: float = c, 
                  transmit: bool = True, **kwargs):
        """
        Plots transmit or receive beam position
        
        :param interval: Interval of signal being transmitted/received
        :type interval: TimeInterval
        :param float, optional v: Velocity of beam, default light speed
        :param bool, optional transmit: Direction of beam. True – Transmit, 
            False – receive, defaults to True
        
        Keyword arguments are passed further to matplotlib.
        
        """
        if transmit:
            d = 1
        else:
            d = -1
        
        line1x = interval.begin + np.array((0, d * self.plot_interval.length))
        line1y = np.array((0 , self.plot_interval.length*v))
        
        line2x = interval.end + np.array((0, d * self.plot_interval.length))
        line2y = np.array((0 , self.plot_interval.length*v))

        
        if "color" not in kwargs:
            kwargs["color"] = self.get_colour(name)

        # Plot beginning of pulse
        self.ax[0].plot(line1x/µs, line1y/km, **kwargs)
        
        # Make sure that end of pulse is in the same colour as the beginning.
            
        # Plot end of pulse
        self.ax[0].plot(line2x/µs, line2y/km, **kwargs)
        
        self.ax[0].xaxis.set_label("Time [µs]")
        self.ax[0].yaxis.set_label("Range [km]")

        self.ax[0].yaxis.set_minor_formatter("{x:.0f}")
        self.ax[0].xaxis.set_minor_formatter("{x:.0f}")
        self.ax[0].tick_params(which = 'major', pad = 15)
        self.ax[0].tick_params(which = 'minor', grid_linewidth = 2, pad = 0)
        
    def transmit(self, name: str, interval: TimeInterval, **kwargs):
        """
        Plots transmit beam position
        
        :param interval: Interval of signal being transmitted
        :type interval: TimeInterval
        
        Keyword arguments are passed further to matplotlib.
        
        """
        self.add_beam(name, interval, v=c, **kwargs)
    def receive(self, name: str, interval: TimeInterval, **kwargs):
        """
        Plots receive beam position
        
        :param interval: Interval of signal being received
        :type interval: TimeInterval
        
        Keyword arguments are passed further to matplotlib.
        
        """
        self.add_beam(name, interval, v=c, transmit=False, **kwargs)   
        
    def state(self, name: str, bar_lengths: Union[list, np.ndarray], 
                     bars_begin_at: Union[list, np.ndarray], **kwargs):
        """
        Plot setting of radar.
        
        :param name: name of setting
        :type name: str
        :param bar_lengths: Lengths of bars
        :type bar_lengths: list or numpy array
        :param bars_begin_at: Position where bars begin
        :type bars_begin_at: list or numpy array
        
        Other (keyword) arguments go directly to plotting function
    
        """
        if "color" not in kwargs:
            kwargs["color"] = self.get_colour(name)
        
        self.ax[1].barh(name, np.asarray(bar_lengths)/µs, 
                 left=np.asarray(bars_begin_at)/µs, **kwargs)
        self.ax[1].xaxis.set_label("Time [µs]")
            
    def add_range_label(self, r: float):
        """
        Adds a label to a certain range as a minor tick
        
        :param float r: range [m]
    
        """
        mt = self.ax[0].get_yticks(minor = True)
        self.ax[0].set_yticks(np.hstack([mt, r/km]), minor = True)
    def add_time_label(self, t: float):
        """
        Adds a label to a certain time as a minor tick
        
        :param float t: time [s]
    
        """
        mt = self.ax[0].get_xticks(minor = True)
        self.ax[0].set_xticks(np.hstack([mt, t/µs]), minor = True) 


    