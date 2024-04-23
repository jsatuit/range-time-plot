

import numpy as np
import matplotlib.pyplot as plt
if __name__ == '__main__':
    import sys
    sys.path.append("..") # Adds current directory to python modules path.
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

def plot_transmit(ax, tx_interval: TimeInterval, plot_interval: TimeInterval, **kwargs):
    """
    Plots transmit beam position
    
    :param matplotlib.axes._axes.Axes ax: Axes object to plot into
    :param signal_interval: Interval of signal being transmitted
    :param plot_interval: Axis limits of time axis
    
    Other keyword arguments go to plotting punctions
    
    """
    plot_t_r(ax, tx_interval, plot_interval, v=c, color='blue', **kwargs)
    
def plot_receive(ax, rx_interval, plot_interval, **kwargs):
    """
    Plots receive beam position
    
    :param matplotlib.axes._axes.Axes ax: Axes object to plot into
    :param TimeInterval signal_interval: Interval of signal being received
    :param TimeInterval plot_interval: Axis limits of time axis
    
    Other keyword arguments go to plotting punctions
    
    """
    if not "color" in kwargs:
        kwargs["color"] = "red"
    
    plot_t_r(ax, rx_interval, plot_interval, v=c, d = -1, **kwargs)
    
def plot_t_r(ax, signal_interval, plot_interval, v=c, d = 1, **kwargs):
    """
    Plots transmit or receive beam position
    
    :param matplotlib.axes._axes.Axes ax: Axes object to plot into
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
    ax.plot(line1x/µs, line1y/km, **kwargs)
    # Plot end of pulse
    ax.plot(line2x/µs, line2y/km, **kwargs)
    
    plot_xlims(ax, plot_interval)
    ax.xaxis.set_label("Time [µs]")
    ax.yaxis.set_label("Range [km]")

    ax.yaxis.set_minor_formatter("{x:.0f}")
    ax.xaxis.set_minor_formatter("{x:.0f}")
    ax.tick_params(which = 'major', pad = 15)
    ax.tick_params(which = 'minor', grid_linewidth = 2, pad = 0)
    
def plot_xlims(ax, plot_interval):
    """Set limits of x axis. """
    ax.set_xlim((plot_interval/µs).as_tuple)
    
def plot_setting(ax, name, bar_lengths, bars_begin_at, plot_interval, **kwargs):
    """
    Plot setting of radar.
    
    :param matplotlib.axes._axes.Axes ax: Axes object to plot into
    :param name: name of setting
    :type name: str
    :param bar_lengths: Lengths of bars
    :type bar_lengths: list or numpy array
    :param bars_begin_at: Position where bars begin
    :type bars_begin_at: list or numpy array
    :param plot_interval: X axis limits
    :type plot_interval: TimeInterval
    
    Other (keyword) arguments go directly to plotting function

    """
    ax.barh(name, np.asarray(bar_lengths)/µs, 
             left=np.asarray(bars_begin_at)/µs, **kwargs)
    plot_xlims(ax, plot_interval)
    ax.xaxis.set_label("Time [µs]")

    
def plot_add_range_label(ax, r):
    """
    Adds a label to a certain range as a minor tick
    
    :param float r: range [m]

    """
    mt = ax.get_yticks(minor = True)
    ax.set_yticks(np.hstack([mt, r/km]), minor = True)
def plot_add_time_label(ax, t):
    """
    Adds a label to a certain time as a minor tick
    
    :param float t: time [s]

    """
    mt = ax.get_xticks(minor = True)
    ax.set_xticks(np.hstack([mt, t/µs]), minor = True) 

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
    plt.grid(which = 'major')
    plot_transmit(transmit, cycle)
    plot_receive(receive, cycle)
    plot_add_range_label(rmin)
    plot_add_range_label(rmax)
    
    plot_add_time_label(transmit.begin)
    plot_add_time_label(transmit.end)
    plot_add_time_label(receive.begin)
    plot_add_time_label(receive.end)
    