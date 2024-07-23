#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import matplotlib.pyplot as plt


from src.experiment import Experiment

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('file.log', mode="w")
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.DEBUG)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

def main(path: str, radar: str, subcycle: int, savepath: str, phaseplot: bool = False):
    """
    Tarlan file plotter. 

    Plots EISCAT KST experiment specified with a .tlan file

    \f

    :param str path: Path to tlan file which to plot
    :param str radar: Which radar to plot for. It might be that experiment doesnt exist for that radar. 
    :param int subcycle: Subcycle to plot. Zero means plot all. Default is 1
    :param str savepath: Path of where to save the figure. If given, figure will 
    not be shown, only saved. If empty, figure will be shown, not saved. Default is empty (show, not save)
    :param bool phaseplot: Plot phases of experiment? Phases of all subcycles will be plotted. Default is False.

    """
    logger.info(f"called program with arguments path={path} and subcycles {subcycle}")
    print(f"Loading and plotting experiment {path}")
    exp = Experiment.from_eiscat_kst(path, radar)
    
    if subcycle == 0:
        f1 = exp.plot()
    else:
        f1 = exp.plot([subcycle])
        
    if phaseplot:
        f2 = exp.plot_phaseshifts()
        
    if savepath:
        f1.fig.savefig(os.path.join(savepath, exp.name + ".png"))
        if phaseplot:
            f2.savefig(os.path.join(savepath, exp.name + "_phase.png"))
    else:
        plt.show()
        

