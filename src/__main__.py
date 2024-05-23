#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from src.main import main


parser = argparse.ArgumentParser(description="Plot EISCAT experiments")
parser.add_argument("path", type=str)
parser.add_argument("subcycle", type=int, nargs = "?", default = 1)
args = parser.parse_args()

main(args.path, args.subcycle)
