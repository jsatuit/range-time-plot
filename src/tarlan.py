#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# from collections import OrderedDict
"""
The Transmit And Receiver LANguage (TARLAN) is the language for the radar controllers
at the EISCAT mainland radars, that are EISCAT UHF and VHF, including receivers
in Kiruna and Sodankylä.

The radar controller controls most of the physical radar equipment, that is 
phase shifting, beams, transmittion, reception, but not antenna steering or 
signal processing.

The dictionary `Tarlan.commands` gives an overview over the commands the system
can run. More infortmation can be found at
https://eiscat.se/scientist/user-documentation/radar-controllers-and-programming-for-the-kst-system/
"""
import warnings
import os

from bisect import insort_left
from typing import Self

from src.experiment import Experiment, Subcycle
from src.tarlanIntervals import IntervalList, TarlanSubcycle
from src.tarlanError import TarlanError
from src.const import km, µs, c

def kst_channels():
    "List of available channels"
    
    chs = []
    for i in range(1,7):
        chs.append(f"CH{i}") 
    return chs



def do_nothing(*args):
    """Dont delete. This function is needed for executing tarlan commands that 
       cant be simulated/transferred or where is would not make sense to 
       implement the function here."""
    pass

class Command:
    """
    Tarlan command.
    
    :param float t: Subcycle time in seconds when command is executed.
    :param str cmd: Command as written in the .tlan file
    :param int line: Line in tlan file. Used for error messages
    
    """
    
    def __init__(self, t: float, cmd: str, line: int = 0):
        """
        
        :param t: Subcycle time in seconds when command is executed.
        :type t: float
        :param cmd: Command as written in the .tlan file
        :type cmd: str
        :param line: Line in tlan file. Used for error messages, defaults to 0.
        :type line: int

        """
        self.t = t
        self.cmd = cmd
        self.line = line
        
    def __lt__(self, other: Self) -> bool:
        # Is used for sorting. Therefore only the time matters
        return self.t < other.t
    
    def __repr__(self):
        return f'Command({self.t}, "{self.cmd}", {self.line})'
    
    def __str__(self):
        return f"{self.line}: {self.t/µs} {self.cmd}"
    
class ParseSubcycle:
    """
    Lists commands in single subcycle. Used for grouping commands from the tlan 
    file. Commands are sorted after execution time
    """
    
    def __init__(self, start_subcycle: float = 0, line: int = 0) -> None:
        """
        
        :param start_subcycle: start of subcycle in seconds, defaults to 0
        :type start_subcycle: float, optional
        :param int, optional line: Codeline where subcycle starts

        """
        self.start = start_subcycle
        self.startline = line
        self.commands = []
        
    def add_command(self, cmd: str) -> None:
        """
        Add command to subcycle. 
        :param cmd: command
        :type cmd: str
        :raises ValueError: if command is above start of subcycle in the tlan 
            file

        """
        if cmd.line > 0 and cmd.line < self.startline:
            raise ValueError(f"The inserted command is from line {cmd.line},"
                             " above the start line {self.startline} of the"
                             " subcycle!")

        insort_left(self.commands, cmd)
                 
            
class Tarlan():
    """
    Class for parsing and handling an TARLAN experiment
    
    :param IntervalList cycle: Begin and end of experiment cycle
    :param IntervalList subycle: Begin and end of experiment subcycles. These
        are defined by when SETTCR <time> is called.
    :param dict[str, IntervalList] streams: Dictionary of all on/off times of 
        the different settings in the radar system controller, among others
        "RF", "CH1".
    :param float end_time: Length of tarlan program in seconds.
    """
    
        
    commands = {
        "CHQPULS": "High output on bit 31 for 2 us, used for synchronization "+
            "with external hardware.",
        "RXPROT": "Enable receiver protector, bit 12 high",
        "RXPOFF": "Disable receiver protector, bit 12 low",
        "LOPROT": "Enable local oscillator protector, bit 6 high",
        "LOPOFF": "Disable local oscillator protector, bit 6 low",
        "BEAMON": "Enable beam in klystron, bit 13 high",
        "BEAMOFF": "Disable beam in klystron, bit 13 low",
        "PHA0": "Set proper phase, bit 4 low",
        "PHA180": "Set proper phase, bit 4 high",
        "CALON": "Tromsø and receivers: Enable noise source for calibration, bit 15 high.",
        "CALOFF": "Tromsø and receivers: Disable noise source, bit 15 low.",
        "HCALON": "Remote receivers: enable noise source in only horisontal "+
            "wave guide, high bit 1 high",
        "HCALOFF": "Remote receivers: disable noise source in only horisontal "+
            "wave guide, high bit 1 low",
        "VCALON": "Remote receivers: enable noise source in only vertical "+
            "wave guide, high bit 1 high",
        "VCALOFF": "Remote receivers: disable noise source in only vertical "+
            "wave guide, high bit 1 low",
        "STC": "Send a interrupt to crate computer to signal that new data are "+
            "available a needs to be taken care of, bit 8 high strobed.",
        "BUFLIP": "Change side of buffer memory in channel boards, bit 17 high strobed.",
        "ALLOFF": "Close sampling gate on all channel boards, bit 10-15 low",
        "REP": "End of tarlan program/repeat cycle",
        
        }
    for i in range(16):
        commands["F" + str(i)] = "Set transmitter frequency, bit 0-3 high"
    for ch in kst_channels():
        commands[ch] = \
            f"Open sampling gate on the referenced channel board, bit {i+9} high"
        commands[ch + "OFF"] = \
            f"Close sampling gate on the referenced channel board, bit {i+9} low"
    
    def __init__(self, filename: str = ""):
        """
        Initializing Tarlan(). If .tlan file is specified, it will be loaded.
        
        :param file_name: Path of tlan file to load. No file is loaded if 
            string is empty, defaults to ""
        :type file_name: str, optional

        """
        self.cycle = IntervalList("CYCLE")
        # self.subcycles = IntervalList("SUBCYCLE")
        self.subcycles = TarlanSubcycle()
        
        self.stream_names = ["RF", "RXPROT", "LOPROT", "CAL", "BEAM", "+", "-"]
        for ch in kst_channels():
            self.stream_names.append(ch)
        self._init_streams()
            
        # Time control
        self.TCR = 0
        self.end_time = 0
        
        if filename:
            self.from_tlan(filename)
    
    def _init_streams(self):
        # Create streams
        self.streams = dict()
        for stream in self.stream_names:
            self.streams[stream] = IntervalList(stream)

    def to_exp(self) -> Experiment:
        """
        Convert loaded tarlan input to Experiment
        
        :raises RuntimeError: If radar controller is not resetted correctly 
            at end of file.
        :raises RuntimeWarning: if transmitter is constantly off.
        :return: object containing experiment information and plotting functions.
        :rtype: Experiment

        """
        exp = Experiment(os.path.basename(self.filename).split(".")[0])

        for i, subcycle_interval in enumerate(self.subcycles.intervals):
            # print(subcycle_interval)
            subcycle = Subcycle(subcycle_interval.begin, subcycle_interval.end)
            
            for stream in self.subcycles.data_intervals[i]:
                if len(stream) == 0:
                    continue
                for interval in self.subcycles.data_intervals[i][stream].intervals:
                    subcycle.add_time(stream, interval)
            
            exp.add_subcycle(subcycle)
        
        return exp

                    
    def from_tlan(self, filename: str = "") -> None:
        """
        Parse tlan file and run Tarlan.exec_cmd() for all commands.
        
        :param filename: Path of tlan file to load, defaults to ""
        :type filename: str, optional
        
        """
        cmd_list = tarlan_parser(filename)
        
        for cmd in cmd_list:
            
            """ Use SETTCR as start and stop of subcycles
            Use SETTCR 0 as start and as continuation of subcycle
            SETTCR 0 is therefore only allowed in two cases: In start or 
            directly before REP. Else, subcycles will be merged without at 
            wrong places.
            """
            if cmd.cmd == "SETTCR":
                
                # First subcycle
                if self.cycle.is_off:
                    self.cycle.turn_on(cmd.t, cmd.line)
                    self.subcycles.turn_on(cmd.t, cmd.line)
                
                # All other subcycles except for that SETTCR that appears 
                # directly before REP command at the end of the file
                elif cmd.t != 0:
                    # Turn off phase shifts at RF turnoff
                    self.PHA_OFF(self.streams["RF"].last_turn_off, cmd.line)
                    self.subcycles.turn_off(cmd.t, cmd.line, self.streams)
                    
                    # Delete connection to last subcycle streams¨
                    self._init_streams()
                    
                    self.subcycles.turn_on(cmd.t, cmd.line)
                self.SETTCR(cmd.t, cmd.line)
            elif cmd.cmd == "REP":
                self.PHA_OFF(cmd.t, cmd.line)
                self.subcycles.turn_off(cmd.t, cmd.line, self.streams)
                self.cycle.turn_off(cmd.t, cmd.line)
            else:
                self.exec_cmd(cmd)
        self.filename = filename
        
    def ALLOFF(self, time: float, line: int):
        """
        Turn off signal reception with all channels
        
        :param time: time [s]
        :type time: float
        :param line: line where the command is found. Used for error handling only.
        :type line: int

        """
        for i in range(1,7):
            CH = "CH"+str(i)
            if self.streams[CH].is_on:
                self.streams[CH].turn_off(time, line)
    
    def PHA0(self, time: float, line: int):
        "Set phase shift of oscillator to 0°"
        if self.streams["+"].is_off:
            self.streams["+"].turn_on(time, line)
            
        if self.streams["-"].is_on:
            self.streams["-"].turn_off(time, line)
            
    def PHA180(self, time: float, line: int):
        "Set phase shift of oscillator to 0°"
        if self.streams["+"].is_on:
            self.streams["+"].turn_off(time, line)
            
        if self.streams["-"].is_off:
            self.streams["-"].turn_on(time, line)
            
    def PHA_OFF(self, time: float, line: int):
        """
        Turn off phase shifts. This is not a TARLAN command, but needed to 
        able to plot phase shifts later.
        """
        for ps in ["+", "-"]:
            if self.streams[ps].is_on:
                self.streams[ps].turn_off(time, line)
            
    def SETTCR(self, time: float, line: int):
        "Set reference time in time control"
        self.TCR = time
        
                
    def exec_cmd(self, cmd: Command):
        """
        «Execute» TARLAN command / import command to experiment
        
        :param cmd: command as pasrsed from the file.
        :type cmd: Command

        """
        if self.cycle.is_off:
            raise TarlanError("The cycle has not been started!", cmd.line)
        
        if self.subcycles.is_off:
            raise TarlanError("No subcycle has been started yet!", cmd.line)
            
        #### Implement TARLAN commands from here ####
        execute_command = {
            "RFON": self.streams["RF"].turn_on,
            "RFOFF": self.streams["RF"].turn_off,
            "RXPROT": self.streams["RXPROT"].turn_on,
            "RXPOFF": self.streams["RXPROT"].turn_off,
            "LOPROT": self.streams["LOPROT"].turn_on,
            "LOPOFF": self.streams["LOPROT"].turn_off,
            "CALON": self.streams["CAL"].turn_on,
            "CALOFF": self.streams["CAL"].turn_off,
            "BEAMON": self.streams["BEAM"].turn_on,
            "BEAMOFF": self.streams["BEAM"].turn_off,
            "PHA0": self.PHA0,
            "PHA180": self.PHA180,
            "ALLOFF": self.ALLOFF,
            "SETTCR": do_nothing,  # Is not handeled here!
            "BUFLIP": do_nothing,  # Too technical here
            "STC": do_nothing,  # Too technical here
            }
        # Add receiver channel commands
        for ch in kst_channels():
            execute_command[ch] = self.streams[ch].turn_on
            execute_command[ch+"OFF"] = self.streams[ch].turn_off
            
        # Handling Frequencies is not yet implemented
        # TODO: handle frequencies
        for f in range(16):
            freq = f"F{f}"
            execute_command[freq] = do_nothing
        
        ''' 
        Silent warnings on setting single bits 4 or 5 in transmit and receive 
        controllers. These go to ADC samplegate, but are not of interest here.
        '''
        for i in [4, 5]:
            for d in ["R", "T"]:
                execute_command[f"B{d}X{i}"] = do_nothing
                execute_command[f"B{d}X{i}OFF"] = do_nothing
        #### Implement TARLAN commands to here ####    
        
        
        
        
        if cmd.cmd in execute_command.keys():
            # print(self.TCR, cmd.t)
            execute_command[cmd.cmd](self.TCR + cmd.t, cmd.line)
        else:
            print(f"Command {cmd.cmd}, called from line {cmd.line} ",
                  "is not implemented yet")
 
    
        
def parse_line(line: str, line_number: int = 0) -> list[Command]:
    """
    Parse single line of Tarlan code.
    
    :param line: line of code
    :type line: str
    :param line_number: line number in file, used for error handling only, defaults to 0
    :type line_number: int, optional
    :raises TarlanError: for invalid commands
    :return: list of Command objects
    :rtype: list[Command]

    """
    time = 0
    commands = []
    
    # Filter away comments
    codeline = line.split("%")[0]
    
    # Unpack arguments
    args = codeline.split()
    
    if len(args) == 0:
        pass
    elif args[0] == "AT":
        # The radar hardware is doing something!
        if len(args) < 3:
            raise TarlanError("Line starting with 'AT' must include time and command(s)!", line_number)
        
        time = float(args[1])*µs
        
        for arg in args[2:]:
            for cmd in arg.split(","):
                commands.append(Command(time, cmd, line_number))
        
        
    elif args[0] == "SETTCR":
        # Set time control ?
        time = float(args[1])*µs
        
        commands = [Command(time, "SETTCR", line_number)]

    else:
        raise TarlanError("Line must start with 'AT' or 'SETTCR'. Use '%' for comments.", line_number)
        
    return commands
        

def tarlan_parser(filename: str = "") -> list[Command]:
    """
    Parse tlan file. Commands are returned in the same order as they appear in 
    the file.
    
    :param filename: filename, defaults to ""
    :type filename: str
    :return: list of Command objects
    :rtype: list[Command]

    """
    cmd_list = []
    with open(filename) as file:
        for il, line in enumerate(file):
            cmds = parse_line(line, il+1)
            for cmd in cmds:
                cmd_list.append(cmd)
                if cmd.cmd == "REP":
                    break
    return cmd_list

