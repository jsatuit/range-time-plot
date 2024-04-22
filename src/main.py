#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import matplotlib.pyplot as plt

from src.experiment import Experiment

@click.command()
@click.argument("path", 
              type = click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
              required = True, 
              default = 9
)
@click.argument("subcycle",
                type = int,
                required = False,
                default = 1,
                )
def main(path, subcycle):
    print(f"Loading and plotting experiment {path}")
    Experiment.from_eiscat_kst(path).subcycles[subcycle-1].plot()
    plt.show()

