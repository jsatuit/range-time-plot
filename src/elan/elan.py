#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module includes some EROS functions to the tcl parser. Also these are badly documented here, but there is an explanation of EROS commands at https://portal.eiscat.se/jussi/eiscat/erosdoc/cmds.html
"""


import datetime
import re

from math import ceil

from src.elan.tcl import TclScope, extend

class Eros(TclScope):
    RCs = ["transmitter","receiver","ion line receiver","plasma line receiver"]
    
    def __init__(self, radar = "", ant = "", master = None, **var):
        super().__init__(master)
        # if "radar" not in var.keys():
        #     raise ValueError("Radar not specified!")
        self._var = var
        if len(radar) > 0:
            self._var["_radar"] = radar
            
            if not ant:
                ant = radar

            self._var["_ant"] = ant

            # Variables sometimes used at ESR
            self._var["32p"] = "32p"==ant
            self._var["42p"] = "42p"==ant
                
        self.__argv = []
        self._starttimes = {
            "e": -1,
            "b": -1,
            "r": -1,
            "t": -1,
            "c": -1,
        }
        
    def _get_time_string(self):
        t = datetime.datetime.now(datetime.timezone.utc)
        tstr = t.strftime('%Y-%M-%d %H:%M:%S.%f')
        return tstr
    def argv(self, *args):
        return ' '.join(self.__argv)
    def armradar(self, args):
        RCNAME = args[0]
        print(f"Set {RCNAME} controller start address and registers and set the",
              "controller waiting for a start pulse.")
    def BLOCK(self, args):
        tstr = self._get_time_string()
        print(f"Enters BLOCK {args[0]} at {tstr} UTC")
        return self.proc(args)
    def callblock(self, args):
        return self.eval(args)
    def disablerecording(self, args = []):
        if self.ISESR() == "True" or len(args) == 0:
            rec = "ion"
        else:
            rec = args[0]
            
        if self.ISESR() == "False":
            if rec == "pla":
                return
            else:
                print("Disabled recording")
        elif rec == "pla":
            print("Disabled recording of plasma line")
        elif rec == "ion":
            print("Disabled recording of ion line")
        elif rec == "all":
            print("Disabled recording of both plasma and ion line")
        else:
            raise ValueError("Wrong argument {rec}!")
    def getstarttime(self, args):
        device = args[0].lower()[0]
        return str(self._starttimes[device])
    def gotoblock(self, args):
        print("Terminate current BLOCK in a running expriment and start a new one.")
        print(f"New BLOCK is called with {' '.join(args)}")
        raise StopIteration(f"gotoblock {' '.join(args)}")
    def isradar(self, args = None):
        if args is None:
            return self._var["_radar"]
        if isinstance(args, str):
            args = [args]
        for arg in args:
            if self._var["_radar"] == arg:
                return str(True)
        return str(False)
    def ISESR(self, *args):return self.isradar("ESR")
    def ISKIR(self, *args):return self.isradar("KIR")
    def ISSOD(self, *args):return self.isradar("SOD")
    def ISUHF(self, *args):return self.isradar("UHF")
    def ISVHF(self, *args):return self.isradar("VHF")
    def loadfilter(self, args):
        line = "ionline"
        # Index of first option
        io = next((i for i, arg in enumerate(args) if arg.startswith("-")), None)
        if "plasmaline".startswith(args[0]):
            line = "plasmaline"
            linearg = 0
        elif "ionline".startswith(args[0]):
            linearg = 0
        else:
            linearg = -1
            
        fil = args[linearg + 1]
        # channel numbers are all decimals, divided by anything else.
        chs = re.findall(r'\d+', args[linearg + 2])
        options = args[io:]
        if "-T" in options:
            SV = "EROS would check (not load) "
        else:
            SV = "Load "
        O = f"filter {fil} for {line} into channels {', '.join(chs)}"
        print(SV + O)
    def _parse_args_op_rec_x_chs(self, args):
        # Parse arguments if they are in the order
        # ?<OPTIONS>? ?<receiver>? <x> <channels>
        x = args[-2]
        channels = re.findall(r'\d+', args[-1])
        receiver = ""
        if len(args) > 2:
            if "plasmaline".startswith(args[-3]):
                receiver = "plasmaline"
            elif "ionline".startswith(args[-3]):
                receiver = "ionline"
            else: 
                receiver = ""
        
        options = [arg[1].lower() for arg in args[0:-2-bool(receiver)]]
        return options, receiver, x, channels
    
    def loadfrequency(self, args):
        options, rec, file, chs = self._parse_args_op_rec_x_chs(args)

        verbose = "verbose "*("v" in options)
        l = "load"*("t" not in options)
        t = "test"*("t" in options)
        c = "and correct "*("e" in options or self.ISESR()=="True")
        u = "uncorrected"*("u" in options or not self.ISESR()=="True")
        v = f"{verbose}{l}{t}".capitalize()
        s = f"{v} {c}frequencies from file {file} {u} into channels {', '.join(chs)}"
        print(s)
    def loadradar(self, args):
        print(f"Load {extend(self.RCs, args[0])} controller")
        for option, value in zip(args[1::2], args[2::2]):
            if option[1] == 'f':
                print(f"load compiled TARLAN programfile {value}")
            elif option[1] == 'l':
                loop_count = int(value)
                print(f"set loopcounter to {loop_count}")
                # it = Loopcount*loop duration (from REP x in .tlan) gives 
                # integration time
            elif option[1] == 's':
                """Since EROS assumes integrationtime to be dividable with 10 ms,
                there may be time inbetween integrationtime and start of next 
                integration loop. This time is the sync count which is given here 
                in 100 ns intervals.
                """
                sync_period = float(value)/10
                print(f"set syncronisation period to {sync_period} µs")
                # TODO: Actually load TLAN to get this information
                rep = 192000  # From manda
        # Ensure that the syncronisation period is correct
        needed_sync = ceil(rep*loop_count/10000)*10000 - rep*loop_count
        if not abs(needed_sync - sync_period) < 0.01:
            print("warning: The experiment needs a syncronisation period of "+
                  str(needed_sync) + f"µs , but {sync_period} µs was given !")
            print("Still, Manda is assumed, so rather load correct tlan first")
    
                
        
        
    def runexperiment(self, args):
        filename = args[0]+".elan"
        self.__argv = args[2:]
        with open(filename) as file:
            script = file.read()
        self(script)
    
    def selectlo(self, args):
        s = "Select local oscillator frequencies: "
        if len(args) == 3:
            s += f"Oscillator {args[0]}, "
        s += f"Path {args[-2]}, "
        s += f"Frequency {args[-1]}."
        print(s)
    def setfrequency(self, args):
        # Of course the docs are right here.
        # Could not setfrequency and loadfrequency have same order of arguments?????
        
        options, rec, freq, chs = self._parse_args_op_rec_x_chs(
            [*args[0:-2], args[-1], args[-2]]
        )
        verbose = "verbose "*("v" in options)
        l = "load"*("t" not in options)
        t = "test"*("t" in options)
        c = "and correct "*("e" in options or self.ISESR()=="True")
        u = " uncorrected"*("u" in options or not self.ISESR()=="True")
        v = f"{verbose}{l}{t}".capitalize()
        s = f"{v} {c}frequencies in channels {', '.join(chs)} to {freq} MHz{u}."
        print(s)
    def startdata(self, args):
        print("Start both correlator and recorder.")
        if args[0] in ["ion", "-ion", "pla", "-pla"]:
            rec = args[0]
            args = args[1:]
        else:
            rec = "ion"
        CorrFile, Expid, Iper = args[0:3]
            
        if self.ISESR() == "False" and rec.endswith("pla"):
            return
        
        if self.ISESR() == "True":
            if len(args) < 4:
                raise ValueError("Must specify antenna (32m or 42m)!")
            else:
                ant = args[3]
        else:
            ant = self._var["_ant"]
            
        
        print(f"Loading file {CorrFile} into correlator.")
        print(f"Uses Expid {Expid}")
        print(f"Integration time is {Iper}")
        print(f"Antenna is {ant}")
                
            
    def startradar(self, args):
        time_spec = args[0]
        if time_spec.capitalize().startswith('E'):
            time_spec = "ETIME"
        print(f"Radar controllers will start at time_spec {time_spec}.",
              "integration period is set to {args[1]} s.")
    def stopdata(self, *args):
        print("Stop data access by stopping both correlator and recorder.")
    def stopradar(self, args):
        print(f"Stop {extend(self.RCs, args[0][1:])} controller.")
    def SYNC(self, args):
        tstr = self._get_time_string()
        print(f"Called SYNC {args[0]} at {tstr}")
    def timestamp(self, args):
        # Convert to int
        time_spec = int(args[-1])
        if time_spec < 0:
            return ""
        # Find format
        if len(args) == 1:
            fmt = "dyhms"
            decs = 1
        else:
            if args[0] == "-3":
                decs = 3
            elif len(args) == 2 and "no" not in args[0]:
                fmt = args[0][1:]  # Ignore '-'
                if fmt[-1] in [str(i) for i in range(10)]:
                    decs = int(fmt[-1])
                    fmt = fmt[0:-1]
                else:
                    decs = 0
            else:
                # Must be -noyear, -nodate or -nofrac
                letters = [arg[3] for arg in args[0:-1]]
                fmt = ""
                if "y" not in letters:
                    fmt += "dy"
                elif "d" not in letters:
                    fmt += "d"
                fmt += "hms"
                if "f" not in letters:
                    decs = 0
                else:
                    decs = 1
        # Convert tcl format to python format
        pf = ""
        if "d" in fmt:
            pf += "%d-%m"
        if "y" in fmt:
            pf += "-%Y "
        pf += "%H:%M:%S"
        pf += "."*bool(decs) + f"%f.{decs}"
            
        
        # Actually make the timestamp
        t = datetime.datetime.fromtimestamp(time_spec)
        return t.strftime(pf)
        
        
                
    def upar(self, args):
        if args[0] == "alias":
            print("Create alias named {args[2]} of user parameter {args[1]}.")
        elif args[0] == 'all':
            if len(args) == 2:
                print("Return all user parameters in EROS (but not here)")
            elif len(args) == 3:
                print("Set/edit all user parameters in EROS (but not here)")
            else:
                raise ValueError("Not more than 3 arguments to upar!")
        elif len(args) == 2:
            print(f"Return user parameter {args[1]} in EROS (but not here)")
        elif len(args) == 3:
            print(f"Set/edit user parameter {args[1]} to {args[2]} (but not here)")
        else:
            raise ValueError("Not more than 3 arguments to upar!")
    def writeexperimentfile(self, args):
        print("Copy following files to {directory_path}:")
        print('-'*25)
        # This is not the correct way to do it. 
        for path in eval(args[0]):
            print(path)
        print('-'*25, '\n')

        
        
