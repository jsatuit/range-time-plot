#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module includes some EROS functions to the tcl parser. Also these are badly documented here, but there is an explanation of EROS commands at https://portal.eiscat.se/jussi/eiscat/erosdoc/cmds.html
"""


import datetime
import difflib
import logging
import os
import re


from math import ceil

from src.elan.tcl import TclScope, extend
from src.kstconfig.nco import Nco

module_logger = logging.getLogger(__name__)


def filefinder(filename:str, ending: str = ".elan"):
    """
    Find file filename. 
    :param filename: experiment filename. May be absolute path (/kst/exp/manda/manda) or relative to
    root of this repository (for example kst/exp/manda/manda). The function will
    also look into folder /kst/exp or kst/exp if they exist.
    
    :type filename: str
    :param str ending: File ending. Default is '.elan'
    :raises FileNotFoundError: If the experiment file is not found in the given 
        directory, or within (subfolders of) (/)kst/exp
    :return: directory, name of experiment, path to experiment
    :rtype: Tuple[str, str, str]

    """
    expname = os.path.splitext(os.path.split(filename)[1])[0]

    if filename.startswith("/kst/exp/"):
        filename = filename[9:]
    # Find elan file
    if not filename.endswith(ending):
        filename += ".elan"
    paths = [
        filename,
        os.path.join("/kst/exp", filename),
        os.path.join("kst", "exp", filename),
    ]
    exists = False
    for path in paths:
        if os.path.isfile(path):
            exists = True
            break
    if not exists:
        raise FileNotFoundError(path)
    
    directory = os.path.split(path)[0]
    return directory, expname, path



class Eros(TclScope):
    RCs = ["transmitter","receiver","ion line receiver","plasma line receiver"]
    
    lo1_default = {"UHF": [812], "VHF": [298, 298], "ESR": [419, 435, 419, 435]}
    lo2_default = {"UHF": [128, 122], "VHF": [84, 84], "ESR": [81.25]*4}
    
    def __init__(self, radar = "", ant = "", master = None, **var):
        super().__init__(master, **var)
        # if "radar" not in var.keys():
        #     raise ValueError("Radar not specified!")
        if master is None:
            self._loadedfiles = dict(zip(["rbin", "tbin", "filter", "fil", "nco"], 
                                     [""]*4+[[""]*6]))
        else:
            self._loadedfiles = master._loadedfiles
        if len(radar) > 0:
            assert radar in ["UHF", "VHF", "ESR", "KIR", "SOD"]
            self._var["_radar"] = radar
            
            if not ant:
                ant = radar

            self._var["_ant"] = ant

            # Variables sometimes used at ESR
            self._var["32p"] = "32p"==ant
            self._var["42p"] = "42p"==ant
            
            self._var["_lo1"] = Eros.lo1_default[radar]
            self._var["_lo2"] = Eros.lo2_default[radar]
            
        module_logger.debug(f"Starting up Eros for {radar} radar")
        
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
    def py_get_loadedfiles(self):
        "Return a dictionary with last loaded files by this EROS instance (including subfunctions)"
        return self._loadedfiles
    def py_get_lo(self, lon: int, MHz: bool = True) -> list[int]:
        """
        Return last loaded frequencies in local oscillator
        
        :param int lon: Which local oscillator to check
        :param bool, optional MHz: If to return frequency in MHz or not (else frequency is given in Hz), defaults to True (that is in MHz)
        :return: Loaded frequencies in selected oscillator
        :rtype: list[int]
        """
        if MHz:
            return self._var[f"_lo{lon}"]
        else:
            return [freq*1e6 for freq in self._var[f"_lo{lon}"]]
    def py_get_tlan(self, di = ""):
        """Guess which .tlan file was used
        
        This is done by finding the last loaded .rbin file* and exchange ending 
        .rbin with .tlan. This should work. 
        
        * compiled .tlan file for reception.
        
        However, there are some potential problems with this:
        - There is no guarantee that the filenames are the same: There
        could be that exp.tlan which was compiled to mohahaha.rbin (and wtf.tbin).
        - There is also a risk that the script is updated while the binary files are not.
        - Transmit-only experiments wont be loaded. Since they would also violate 
        rules EISCAT blue book and thereby not run, this will only happen if 
        the experiment is not programmed properly.
            
        We could also have looked at .tbin file, but since the remote receivers 
        dont transmit, the .tbin file would never be loaded.
        """
        rbin_path = self._loadedfiles["rbin"]
        directory, rbin = os.path.split(rbin_path)
        if di:
            directory = di
        # Find tlan from rbin. 
        tlans = []
        with os.scandir(directory) as iterator:
            for entry in iterator:
                if entry.name.endswith(".tlan") and entry.is_file():
                    tlans.append(entry.name)
                    
        #Use that tlan file that has name closest to rbin
        try:
            tlan_name = difflib.get_close_matches(rbin, tlans, n=1)[0]
        except IndexError as e:
            print("rbin:", rbin) 
            print(tlans)
            raise e
        return tlan_name
        
    def argv(self, *args):
        return ' '.join(self.__argv)
    def armradar(self, args):
        RCNAME = args[0]
        print(f"Set {RCNAME} controller start address and registers and set the",
              "controller waiting for a start pulse.")
    def block(self, args):
        tstr = self._get_time_string()
        print(f"Enters BLOCK {args[0]} at {tstr} UTC")
        return self.proc(args)
    def callblock(self, args):
        # Do the work
        ret = self.eval(args)
        
        # Take over loaded files from block
        # Calling a proc/block gives the last entry of the log the scope of the 
        # proc execution. Thereby we have access to the list of loaded files
        self._loadedfiles = {**self._loadedfiles, **self._log[-1]["scope"]._loadedfiles}
        return ret
    def disablerecording(self, args = []):
        if self.isesr() == "True" or len(args) == 0:
            rec = "ion"
        else:
            rec = args[0]
            
        if self.isesr() == "False":
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
    def disp(self, args):
        disp_strings = []
        disp_options = [[]]
        for arg in args:
            if arg.startswith("-"):
                disp_options[-1].append(arg)
            else:
                disp_strings += arg
                disp_options.append([])
        print(disp_options)
        print(disp_strings)
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
    def isesr(self, *args):return self.isradar("ESR")
    def iskir(self, *args):return self.isradar("KIR")
    def issod(self, *args):return self.isradar("SOD")
    def isuhf(self, *args):return self.isradar("UHF")
    def isvhf(self, *args):return self.isradar("VHF")
    def loadfile(self, *args):
        return self.source(args)
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
        self._loadedfiles["filter"] = fil
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
        for ch in chs:
            self._loadedfiles["nco"][int(ch)-1] = file

        verbose = "verbose "*("v" in options)
        l = "load"*("t" not in options)
        t = "test"*("t" in options)
        c = "and correct "*("e" in options or self.isesr()=="True")
        u = "uncorrected"*("u" in options or not self.isesr()=="True")
        v = f"{verbose}{l}{t}".capitalize()
        s = f"{v} {c}frequencies from file {file} {u} into channels {', '.join(chs)}"
        print(s)
        module_logger.info(s)
    
    def loadradar(self, args):
        print(f"Load {extend(self.RCs, args[0])} controller")
        for option, value in zip(args[1::2], args[2::2]):
            if option[1] == 'f':
                print(f"load compiled TARLAN programfile {value}")
                tbin_or_rbin = extend(["tbin", "rbin"], args[0][0])
                self._loadedfiles[tbin_or_rbin] = value

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
    def logbook(self, args):
        print(f"Print {args} into logbook")
              
    def mount(self, args):
        print("Mounts disk", args, ". This should not be done in an elan script!")
    def readfrequencyfile(self, args):
        file = args[0]
        addrs = args[1]
        if len(args) > 2:
            print("Implementation does not support more than one frequency at the time.")
        try:
            path = filefinder(file, ".nco")[-1]
        except FileNotFoundError:
            print(f"Tried to read frequency file {file}, but that file does not exist!")
            print("Frequencies were not loaded!")
            return ""
        with open(path) as file:
            lines = file.read()
        freqs = Nco.parse_nco(lines)
        module_logger.debug(f"Loaded frequencies {freqs}")
        return str(freqs[int(addrs)])
        
        
        
    def runexperiment(self, args):
        if args[0].endswith(".elan"):
            filename = args[0]
        else:
            filename = args[0]+".elan"
        self.__argv = args[2:]
        with open(filename) as file:
            script = file.read()
        self(script)
    
    def selectlo(self, args):
        path = args[-2]  # ion/pla (UHF), I/II or A/B (VHF), or <too complicated to show here> (ESR)
        f = int(args[-1])  # MHz
        
        # Specify which oscillator to use as a number
        # UHF: 1 - ion, 2 - pla
        # VHF: 1 – I/A, 2 - II/B
        # ESR: 1 – P1/U32/32U/U32m/U, 2 – P2/D32/32D/D32m/D, 3 – P3/U42/42U/U42m, 4 – P4/D42/42D/D42m
        pathsUHF = dict(zip(["i", "ion", "1", "p", "pla", "2"], [1]*3+[2]*3))
        pathsVHF = dict(zip(["I", "A", "II", "B"], [1]*2+[2]*2))
        pathsESR = dict(zip
                        
                        (["P1", "U32", "32U", "U32m", "U", 
                          "P2", "D32", "32D", "D32m", "D", 
                          "P3", "U42", "42U", "U42m", 
                          "P4", "D42", "42U", "U42m"], [1]*5 + [2]*5 + [3]*4 + [4]*4
                         ))
        if self.isuhf() == "True":
            pathnr = pathsUHF[path]
        elif self.isvhf() == "True":
            pathnr = pathsVHF[path]
        elif self.isesr() == "True":
            pathnr = pathsESR[path]
        else:
            raise RuntimeError("You are at no radar ???")
            
                
        
        s = "Select local oscillator frequencies: "
        if len(args) == 3:
            lon = int(args[0][-1])
            assert lon in [1, 2]
            s += f"Oscillator {args[0]}, "
        elif self.isuhf() == "True":
            lon = 2  # At UHF, only lo2 can be configured
        elif self.isesr() == "True":
            lon = 1  # At ESR, only lo1 can be configured
        else:
            raise ValueError("At VHF, the local oscillafor must be specified!")
            
        s += f"Path {path}, "
        s += f"Frequency {f}."
        print(s)
            
        self._var[f"_lo{lon}"][pathnr-1] = f
    def setfrequency(self, args):
        # Of course the docs are right here.
        # Could not setfrequency and loadfrequency have same order of arguments?????
        
        options, rec, freq, chs = self._parse_args_op_rec_x_chs(
            [*args[0:-2], args[-1], args[-2]]
        )
        verbose = "verbose "*("v" in options)
        l = "load"*("t" not in options)
        t = "test"*("t" in options)
        c = "and correct "*("e" in options or self.isesr()=="True")
        u = " uncorrected"*("u" in options or not self.isesr()=="True")
        v = f"{verbose}{l}{t}".capitalize()
        s = f"{v} {c}frequencies in channels {', '.join(chs)} to {freq} MHz{u}."
        print(s)
    def setpanelpath(self, args):
        if self.isvhf == "True":
            if len(args) == 0:
                print("Query panel path")
            elif args[0].lower() == "split":
                print("Send data from panel I and II to ADC 1 and from III and IV to ADC 2")
            elif args[0].lower() == "allA":
                print("Send data from all panels to ADC 1")
            elif args[0].lower() == "allB":
                print("Send data from all panels to ADC 2")
            else:
                print("Did not understand panel path", args[0])
    def startdata(self, args):
        print("Start both correlator and recorder.")
        if args[0] in ["ion", "-ion", "pla", "-pla"]:
            rec = args[0]
            args = args[1:]
        else:
            rec = "ion"
        CorrFile, Expid, Iper = args[0:3]
            
        if self.isesr() == "False" and rec.endswith("pla"):
            return
        
        if self.isesr() == "True":
            if len(args) < 4:
                raise ValueError("Must specify antenna (32m or 42m)!")
            else:
                ant = args[3]
        else:
            ant = self._var["_ant"]
        
        self._loadedfiles["fil"] = CorrFile

        
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
        
        controller = args[0][int(args[0].startswith("-")):]
        
        if "all".startswith(controller):
            print("Stop all radar controllers.")
        else:
            print(f"Stop {extend(self.RCs, controller)} controller.")
    def sync(self, args):
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
        
    def transferlo(self, args):
        print("Transfers control of local oscillator (LO). LO control is not checked here.")
                
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
        elif len(args) == 1:
            print(f"Return user parameter {args[0]}. This implementation always returns zero!")
            return "0"
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

        
        
