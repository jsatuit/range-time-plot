#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import matplotlib.pyplot as plt

from src.experiment import Experiment

@click.command()
@click.argument("path", 
              type = click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
              required = True, 
              default = 9,
)
@click.argument("subcycle",
                type = int,
                required = False,
                default = 1,
                )
def main(path: str, subcycle: int):
    """
    Tarlan file plotter. 
    
    Plots EISCAT KST experiment specified with a .tlan file
    
    \f
    
    :param str path: Path to tlan file which to plot
    :param int subcycle: Subcycle to plot. Zero means plot all.

    """
    print(f"Loading and plotting experiment {path}")
    if subcycle == 0:
        Experiment.from_eiscat_kst(path).plot()
    else:
        Experiment.from_eiscat_kst(path).subcycles[subcycle-1].plot()
    plt.show()

