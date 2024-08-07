#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from src.main import main


parser = argparse.ArgumentParser(description="Plot EISCAT experiments")
parser.add_argument("path", type=str)
parser.add_argument("radar", type=str, nargs = "?", choices = ['UHF', 'VHF'], default="UHF")
parser.add_argument("subcycle", type=int, nargs = "?", default = 1)
parser.add_argument("savepath", type=str, nargs = "?", default = "")
parser.add_argument("--phase", action="store_true")
args = parser.parse_args()

main(args.path, args.radar, args.subcycle, args.savepath, args.phase)
