#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
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

def main(path: str, subcycle: int, savepath: str):
    """
    Tarlan file plotter. 

    Plots EISCAT KST experiment specified with a .tlan file

    \f

    :param str path: Path to tlan file which to plot
    :param int subcycle: Subcycle to plot. Zero means plot all. Default is 1
    :param str savepath: Path of where to save the figure. If given, figure will 
    not be shown, only saved. If empty, figure will be shown, not saved. Default is empty (show, not save)

    """
    logger.info(f"called program with arguments path={path} and subcycles {subcycle}")
    print(f"Loading and plotting experiment {path}")
    if subcycle == 0:
        Experiment.from_eiscat_kst(path).plot()
    else:
        Experiment.from_eiscat_kst(path).plot([subcycle])
        
    if savepath:
        plt.savefig(savepath)
    else:
        plt.show()
        

