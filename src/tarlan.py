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
import numpy as np

from warnings import warn
from typing import Self

from src.phaseshifter import PhaseShifter
from src.tarlanIntervals import IntervalList, TarlanSubcycle
from src.tarlanError import TarlanError, TarlanWarning
from src.const import km, µs, c

tarlan_command_docstring =\
""":param time: time [s]
:type time: float
:param line: line where the command is found. Used for error handling only.
:type line: int"""
"""Docstring ito be inserted to all tarlan commands."""



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
    
        
    command_docs = {
        "CHQPULS": "High output on bit 31 for 2 us, used for synchronization "+
            "with external hardware.",
        "RXPROT": "Enable receiver protector, bit 12 high",
        "RXPOFF": "Disable receiver protector, bit 12 low",
        "LOPROT": "Enable local oscillator protector, bit 6 high",
        "LOPOFF": "Disable local oscillator protector, bit 6 low",
        "BEAMON": "Enable beam in klystron, bit 13 high",
        "BEAMOFF": "Disable beam in klystron, bit 13 low",
        "RFON": "Enable RF output, bit 11 high",
        "RFOFF": "Disable RF output, bit 11 low",
        "PHA0": "Set proper phase, bit 4 low",
        "PHA180": "Set proper phase, bit 4 high",
        "CALON": "Tromsø and receivers: Enable noise source for calibration, bit 15 high.",
        "CAL100": "Not documented. Propably same as CALON",
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
        "SETTCR": "Set reference time in time control?",
        }
    for i in range(16):
        command_docs["F" + str(i)] = "Set transmitter frequency, bit 0-3 high"
    for ch in kst_channels():
        command_docs[ch] = \
            f"Open sampling gate on the referenced channel board, bit {i+9} high"
        command_docs[ch + "OFF"] = \
            f"Close sampling gate on the referenced channel board, bit {i+9} low"
    for i in range(32):
        command_docs["BRX" + str(i)] = f"Set bit {i} on receiver controller. "+\
            "No checks are made."
        command_docs["BRX" + str(i) + "OFF"] = f"Set bit {i} on receiver controller. "+\
            "No checks are made. "
        command_docs["BTX" + str(i)] = f"Set bit {i} on transmitter controller. "+\
            "No checks are made. Use with caution."
        command_docs["BTX" + str(i) + "OFF"] = f"Set bit {i} on transmitter controller. "+\
            "No checks are made. Use with caution."
        
    def __init__(self, filename: str = ""):
        """
        Initializing Tarlan(). If .tlan file is specified, it will be loaded.
        
        :param file_name: Path of tlan file to load. No file is loaded if 
            string is empty, defaults to ""
        :type file_name: str, optional

        """
        self.cycle = IntervalList("CYCLE")
        # self.subcycle_list = IntervalList("SUBCYCLE")
        self.subcycle_list = TarlanSubcycle()
        self.phaseshifter = PhaseShifter()
        
        self.stream_names = ["RF", "RXPROT", "LOPROT", "CAL", "BEAM"]
        for ch in kst_channels():
            self.stream_names.append(ch)
        self._init_streams()
        self._generate_commands()
        self._check_command_docs()
        self._loaded_FIR = False
            
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
                    self.subcycle_list.turn_on(cmd.t, cmd.line)
                    
                
                # All other subcycles except for that SETTCR that appears 
                # directly before REP command at the end of the file
                elif cmd.t != 0:
                    # Turn off phase shifts at end of subcycle
                    # self.PHA_OFF(cmd.t, cmd.line)
                    self.subcycle_list.turn_off(cmd.t, cmd.line, self.streams)
                    
                    # Delete connection to last subcycle streams
                    self._init_streams()
                    
                    self.subcycle_list.turn_on(cmd.t, cmd.line)
                self.SETTCR(cmd.t, cmd.line)
            elif cmd.cmd == "REP":
                # self.PHA_OFF(cmd.t, cmd.line)
                self.subcycle_list.turn_off(cmd.t, cmd.line, self.streams)
                # Delete connection to last subcycle streams
                self._init_streams()
                self.cycle.turn_off(cmd.t, cmd.line)
            else:
                self.exec_cmd(cmd)
        self.filename = filename
        
    def ALLOFF(self, time: float, line: int):
        f"""
        Turn off signal reception with all channels
        
        {tarlan_command_docstring}

        """
        for i in range(1,7):
            CH = "CH"+str(i)
            if self.streams[CH].is_on:
                self.streams[CH].turn_off(time, line)
                
    def STFIR(self, time: float, line: int):
        if self._loaded_FIR > 0:
            warn(f"STFIR was called on line {line}, but FIR filters are "+\
                 "loaded already!", TarlanWarning)
        else:
            self._loaded_FIR = time
            
    def SETTCR(self, time: float, line: int):
        "Set reference time in time control"
        self.TCR = time
        
        
    def _generate_commands(self):
        #"""Implement other TARLAN commands.
        #
        #These are:
        #    
        #"""
        
        
        #### Implement TARLAN commands from here ####
        commands = {
            "RFON": self.streams["RF"].turn_on,
            "RFOFF": self.streams["RF"].turn_off,
            "RXPROT": self.streams["RXPROT"].turn_on,
            "RXPOFF": self.streams["RXPROT"].turn_off,
            "LOPROT": self.streams["LOPROT"].turn_on,
            "LOPOFF": self.streams["LOPROT"].turn_off,
            "CALON": self.streams["CAL"].turn_on,
            "CAL100": self.streams["CAL"].turn_on,
            "CALOFF": self.streams["CAL"].turn_off,
            "BEAMON": self.streams["BEAM"].turn_on,
            "BEAMOFF": self.streams["BEAM"].turn_off,
            "PHA0": self.phaseshifter.PHA0,
            "PHA180": self.phaseshifter.PHA180,
            "ALLOFF": self.ALLOFF,
            "STFIR": self.STFIR,
            "SETTCR": do_nothing,  # Is not handeled here!
            "BUFLIP": do_nothing,  # Too technical here
            "STC": do_nothing,  # Too technical here
            }
        # Add receiver channel commands
        for ch in kst_channels():
            commands[ch] = self.streams[ch].turn_on
            commands[ch+"OFF"] = self.streams[ch].turn_off
            
        # Handling Frequencies is not yet implemented
        # TODO: handle frequencies
        for f in range(16):
            freq = f"F{f}"
            commands[freq] = do_nothing
        
        ''' 
        Silent warnings on setting single bits 4 or 5 in transmit and receive 
        controllers. These go to ADC samplegate, but are not of interest here.
        '''
        for i in [4, 5]:
            for d in ["R", "T"]:
                commands[f"B{d}X{i}"] = do_nothing
                commands[f"B{d}X{i}OFF"] = do_nothing
        #### Implement TARLAN commands to here ####  
        self.commands = commands
        
    def _check_command_docs(self):
        # Check that all commands have docstring
        for cmd in self.commands.keys():
            if cmd not in self.command_docs.keys():
                print("Command", cmd, "has no docstring!")
        
        
    def exec_cmd(self, cmd: Command):
        """
        «Execute» TARLAN command / import command to experiment
        
        :param cmd: command as pasrsed from the file.
        :type cmd: Command

        """
        if self.cycle.is_off:
            raise TarlanError("The cycle has not been started!", cmd.line)
        
        if self.subcycle_list.is_off:
            raise TarlanError("No subcycle has been started yet!", cmd.line)
            
        # Has to be done again and again because python does some strange 
        # function saving?
        self._generate_commands()
            
        if cmd.cmd in self.commands.keys():
            # print(self.TCR, cmd.t)
            self.commands[cmd.cmd](self.TCR + cmd.t, cmd.line)
        else:
            warn(f"Command {cmd.cmd}, called from line {cmd.line} "+\
                  "is not implemented yet", TarlanWarning)
    def baud_length(self) -> float:
        """
        Estimate baud length.
        
        Algorithm:
        - Use times when is the transmit in one phase and calculate the largest 
        common divisor of those. This should in most cases be the baud length.
        
        The computation fails if the bauds need accuracy of better than 1 ns.
        If that happens, the function must be changed accordingly (three 
        hard-coded numbers must become larger)
        
        :raises RuntimeError: If needed accuracy is not met.
        :return: baud length [s]
        :rtype: float

        """
        # length of single phase intervals
        phase_len = []
        for s in ["+", "-"]:
            for subcycle in self.subcycle_list.data_intervals:
                for length in subcycle[s].intervals.lengths:
                    phase_len.append(length)
        
        # Sadly, function calculating gcd does not accept floating point numbers.
        # Therefore we multiply with a milliard and hope for integers. This means
        # that there cant be any bauds (or intervals) with accuracy better than 
        # 1 nanosecond.
        pla = np.asarray(phase_len)
        phase_len_ns = np.rint(pla*1e9).astype(int)
        if not np.all(phase_len_ns - pla*1e9 < 0.5):
            msg = "Could not round array to integers! This propably means that"\
            " an better accuracy than 1 nanosecond is needed."
            raise RuntimeError(msg)
        
        return np.gcd.reduce(phase_len_ns)/1e9
    
        
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

